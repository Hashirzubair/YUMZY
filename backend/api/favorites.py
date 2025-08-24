from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.security import get_current_user
from models.user import User
from services.recipe_service import RecipeService
from schemas.favorite import FavoriteCreate, FavoriteResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/favorites", tags=["Favorites"])

@router.get("", response_model=List[FavoriteResponse])
async def get_user_favorites(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's favorite recipes"""
    
    service = RecipeService(db)
    return service.get_user_favorites(current_user.id, page, limit)

@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add recipe to favorites"""
    
    service = RecipeService(db)
    return service.add_to_favorites(
        recipe_id=favorite_data.recipe_id,
        user_id=current_user.id,
        notes=favorite_data.notes
    )

@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove recipe from favorites"""
    
    service = RecipeService(db)
    service.remove_from_favorites(recipe_id, current_user.id)

@router.get("/{recipe_id}/check")
async def check_favorite_status(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if recipe is in user's favorites"""
    
    service = RecipeService(db)
    is_favorited = service.is_recipe_favorited(recipe_id, current_user.id)
    
    return {"recipe_id": recipe_id, "is_favorited": is_favorited}