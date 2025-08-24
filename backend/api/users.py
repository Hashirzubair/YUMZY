from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.security import get_current_user
from models.user import User
from services.user_service import UserService
from schemas.user import UserResponse, UserUpdate
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get public user profile by ID"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        bio=user.bio,
        is_vegetarian=user.is_vegetarian,
        is_vegan=user.is_vegan,
        is_gluten_free=user.is_gluten_free,
        preferred_cuisines=user.preferred_cuisines or [],
        cooking_skill_level=user.cooking_skill_level,
        created_at=user.created_at
        # Email and other private info excluded for public profile
    )

@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get public user statistics"""
    
    service = UserService(db)
    return service.get_user_stats(user_id)

@router.get("/me/analytics")
async def get_user_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for current user"""
    
    service = UserService(db)
    return service.get_user_analytics(current_user.id)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    
    service = UserService(db)
    return service.update_user(current_user.id, user_update)

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user account"""
    
    service = UserService(db)
    service.delete_user(current_user.id)