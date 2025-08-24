from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.security import get_current_user, get_current_user_optional
from models.user import User
from models.recipe import Recipe
from models.ingredient import Ingredient
from models.rating import Rating
from services.recipe_service import RecipeService
from schemas.recipe import (
    RecipeCreate, RecipeUpdate, RecipeResponse, RecipeDetailed,
    RecipeListResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recipes", tags=["Recipes"])

@router.get("", response_model=RecipeListResponse)
async def get_recipes(
    page: int = 1,
    limit: int = 20,
    cuisine_type: Optional[str] = None,
    meal_type: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    max_prep_time: Optional[int] = None,
    is_vegetarian: Optional[bool] = None,
    is_vegan: Optional[bool] = None,
    is_gluten_free: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get recipes with optional filters"""
    
    service = RecipeService(db)
    
    filters = {
        "cuisine_type": cuisine_type,
        "meal_type": meal_type,
        "difficulty_level": difficulty_level,
        "max_prep_time": max_prep_time,
        "is_vegetarian": is_vegetarian,
        "is_vegan": is_vegan,
        "is_gluten_free": is_gluten_free
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    return service.get_recipes(
        page=page,
        limit=limit,
        filters=filters,
        user_id=current_user.id if current_user else None
    )

@router.post("", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_data: RecipeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new recipe"""
    
    service = RecipeService(db)
    return service.create_recipe(recipe_data, current_user.id)

@router.get("/{recipe_id}", response_model=RecipeDetailed)
async def get_recipe(
    recipe_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get detailed recipe information"""
    
    service = RecipeService(db)
    
    # Track recipe view in background
    background_tasks.add_task(
        service.track_recipe_view,
        recipe_id,
        current_user.id if current_user else None
    )
    
    return service.get_recipe_detailed(
        recipe_id, 
        current_user.id if current_user else None
    )

@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update recipe (only by recipe author)"""
    
    service = RecipeService(db)
    return service.update_recipe(recipe_id, recipe_update, current_user.id)

@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete recipe (only by recipe author)"""
    
    service = RecipeService(db)
    service.delete_recipe(recipe_id, current_user.id)

@router.get("/{recipe_id}/similar", response_model=List[RecipeResponse])
async def get_similar_recipes(
    recipe_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get recipes similar to the specified recipe"""
    
    service = RecipeService(db)
    return service.get_similar_recipes(recipe_id, limit)

@router.get("/user/{user_id}", response_model=List[RecipeResponse])
async def get_user_recipes(
    user_id: int,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get recipes created by a specific user"""
    
    service = RecipeService(db)
    return service.get_user_recipes(user_id, page, limit)

@router.get("/{recipe_id}/ratings")
async def get_recipe_ratings(
    recipe_id: int,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get ratings for a recipe"""
    
    service = RecipeService(db)
    return service.get_recipe_ratings(recipe_id, page, limit)