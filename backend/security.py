from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import secrets
import re

from backend.config import settings
from backend.models import User, get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class SecurityUtils:
    """Security utilities for authentication and authorization"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Validate password strength based on requirements"""
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
            )
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter"
            )
        
        if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r"\d", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one number"
            )
        
        if settings.PASSWORD_REQUIRE_SYMBOLS and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one special character"
            )
        
        return True
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return payload
        
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate password reset token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate email verification token"""
        return secrets.token_urlsafe(32)

# Security utilities instance
security_utils = SecurityUtils()

# Convenience functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return security_utils.verify_password(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return security_utils.get_password_hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return security_utils.create_access_token(data, expires_delta)

def create_refresh_token(data: dict) -> str:
    return security_utils.create_refresh_token(data)

# Authentication dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = security_utils.verify_token(credentials.credentials)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Get user from database
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise credentials_exception
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    except HTTPException:
        raise
    except Exception:
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user

async def get_current_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current verified user"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not verified"
        )
    return current_user

# Optional authentication (for public endpoints that can show personalized content if user is logged in)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if credentials is None:
        return None
    
    try:
        # Verify token
        payload = security_utils.verify_token(credentials.credentials)
        username: str = payload.get("sub")
        if username is None:
            return None
        
        # Get user from database
        user = db.query(User).filter(User.username == username).first()
        if user is None or not user.is_active:
            return None
        
        return user
    
    except:
        return None

# Permission checking utilities
class Permissions:
    """Permission checking utilities"""
    
    @staticmethod
    def check_recipe_ownership(user: User, recipe_author_id: int) -> bool:
        """Check if user owns the recipe"""
        return user.id == recipe_author_id
    
    @staticmethod
    def check_shopping_list_ownership(user: User, list_user_id: int) -> bool:
        """Check if user owns the shopping list"""
        return user.id == list_user_id
    
    @staticmethod
    def check_collection_ownership(user: User, collection_user_id: int) -> bool:
        """Check if user owns the collection"""
        return user.id == collection_user_id
    
    @staticmethod
    def can_edit_recipe(user: User, recipe_author_id: int) -> bool:
        """Check if user can edit recipe"""
        return user.id == recipe_author_id
    
    @staticmethod
    def can_delete_recipe(user: User, recipe_author_id: int) -> bool:
        """Check if user can delete recipe"""
        return user.id == recipe_author_id
    
    @staticmethod
    def can_view_private_recipe(user: User, recipe_author_id: int, is_published: bool) -> bool:
        """Check if user can view private recipe"""
        return is_published or user.id == recipe_author_id

# Permission decorators and dependencies
def require_recipe_ownership(user: User, recipe_author_id: int):
    """Require recipe ownership"""
    if not Permissions.check_recipe_ownership(user, recipe_author_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this recipe"
        )

def require_shopping_list_ownership(user: User, list_user_id: int):
    """Require shopping list ownership"""
    if not Permissions.check_shopping_list_ownership(user, list_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this shopping list"
        )

# Rate limiting utilities
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, identifier: str, limit: int, window: int) -> bool:
        """Check if request is allowed within rate limit"""
        now = datetime.utcnow()
        
        # Clean old entries
        cutoff = now - timedelta(seconds=window)
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier] 
                if req_time > cutoff
            ]
        else:
            self.requests[identifier] = []
        
        # Check rate limit
        if len(self.requests[identifier]) >= limit:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining_requests(self, identifier: str, limit: int) -> int:
        """Get remaining requests in current window"""
        current_requests = len(self.requests.get(identifier, []))
        return max(0, limit - current_requests)

# Global rate limiter instance
rate_limiter = RateLimiter()

# Rate limiting dependency
async def check_rate_limit(request, user: Optional[User] = None):
    """Check rate limit for request"""
    if not settings.ENABLE_RATE_LIMITING:
        return
    
    # Use user ID if available, otherwise use IP address
    identifier = f"user_{user.id}" if user else f"ip_{request.client.host}"
    
    # Check per-minute rate limit
    if not rate_limiter.is_allowed(identifier, settings.RATE_LIMIT_PER_MINUTE, 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Too many requests per minute."
        )
    
    # Check per-hour rate limit
    if not rate_limiter.is_allowed(f"{identifier}_hour", settings.RATE_LIMIT_PER_HOUR, 3600):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Too many requests per hour."
        )

# API key utilities (for external integrations)
class APIKeyManager:
    """API key management utilities"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a new API key"""
        return f"yumzy_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def validate_api_key(api_key: str, db: Session) -> Optional[User]:
        """Validate API key and return associated user"""
        # This would typically check against a database table of API keys
        # For now, we'll return None as API keys are not implemented in the basic version
        return None

# Session management
class SessionManager:
    """User session management"""
    
    @staticmethod
    def create_session(user: User) -> Dict[str, str]:
        """Create user session tokens"""
        access_token = create_access_token(data={"sub": user.username})
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    @staticmethod
    def refresh_session(refresh_token: str) -> Dict[str, str]:
        """Refresh user session using refresh token"""
        try:
            payload = security_utils.verify_token(refresh_token, "refresh")
            username = payload.get("sub")
            
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Create new access token
            access_token = create_access_token(data={"sub": username})
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )