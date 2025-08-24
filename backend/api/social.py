from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.security import get_current_user
from models.user import User
from services.recipe_service import RecipeService
from schemas.rating import RatingCreate, RatingResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/social", tags=["Social Features"])

@router.post("/ratings", response_model=RatingResponse, status_code=201)
async def create_rating(
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate a recipe"""
    
    service = RecipeService(db)
    return service.create_rating(rating_data, current_user.id)

@router.get("/ratings/{recipe_id}", response_model=List[RatingResponse])
async def get_recipe_ratings(
    recipe_id: int,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get ratings for a recipe"""
    
    service = RecipeService(db)
    return service.get_recipe_ratings(recipe_id, page, limit)

@router.put("/ratings/{rating_id}", response_model=RatingResponse)
async def update_rating(
    rating_id: int,
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's rating"""
    
    service = RecipeService(db)
    return service.update_rating(rating_id, rating_data, current_user.id)

@router.delete("/ratings/{rating_id}", status_code=204)
async def delete_rating(
    rating_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user's rating"""
    
    service = RecipeService(db)
    service.delete_rating(rating_id, current_user.id)

@router.get("/share/{recipe_id}")
async def get_share_url(
    recipe_id: int,
    platform: str = "general",
    db: Session = Depends(get_db)
):
    """Get shareable URL for recipe"""
    
    service = RecipeService(db)
    return service.get_share_url(recipe_id, platform)

@router.post("/share/{recipe_id}")
async def share_recipe(
    recipe_id: int,
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track recipe share"""
    
    service = RecipeService(db)
    return service.track_recipe_share(recipe_id, platform, current_user.id)