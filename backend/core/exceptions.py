from typing import Optional, Dict, Any
from fastapi import HTTPException, status

class YumzyException(HTTPException):
    """Custom exception class for YUMZY application"""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)

# Authentication Exceptions
class AuthenticationError(YumzyException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="AUTH_FAILED"
        )

class AuthorizationError(YumzyException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="ACCESS_DENIED"
        )

# User Exceptions
class UserNotFoundError(YumzyException):
    def __init__(self, message: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="USER_NOT_FOUND"
        )

class UserAlreadyExistsError(YumzyException):
    def __init__(self, message: str = "User already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="USER_EXISTS"
        )

# Recipe Exceptions
class RecipeNotFoundError(YumzyException):
    def __init__(self, message: str = "Recipe not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="RECIPE_NOT_FOUND"
        )

class RecipeAccessDeniedError(YumzyException):
    def __init__(self, message: str = "Recipe access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="RECIPE_ACCESS_DENIED"
        )

# Ingredient Exceptions
class IngredientNotFoundError(YumzyException):
    def __init__(self, message: str = "Ingredient not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="INGREDIENT_NOT_FOUND"
        )

# Favorite Exceptions
class FavoriteNotFoundError(YumzyException):
    def __init__(self, message: str = "Recipe not in favorites"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="FAVORITE_NOT_FOUND"
        )

class DuplicateFavoriteError(YumzyException):
    def __init__(self, message: str = "Recipe already in favorites"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="DUPLICATE_FAVORITE"
        )

# Shopping List Exceptions
class ShoppingListNotFoundError(YumzyException):
    def __init__(self, message: str = "Shopping list not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="SHOPPING_LIST_NOT_FOUND"
        )

class ShoppingListAccessDeniedError(YumzyException):
    def __init__(self, message: str = "Shopping list access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="SHOPPING_LIST_ACCESS_DENIED"
        )

# Validation Exceptions
class ValidationError(YumzyException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )

# Database Exceptions
class DatabaseError(YumzyException):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_code="DATABASE_ERROR"
        )