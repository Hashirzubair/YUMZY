from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.security import get_current_user_optional
from models.user import User
from services.search_service import SearchService
from schemas.search import SearchResponse, IngredientResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])

@router.get("", response_model=SearchResponse)
async def search_recipes(
    query: Optional[str] = Query(None, description="Search query for recipe titles and descriptions"),
    ingredients: Optional[str] = Query(None, description="Comma-separated list of ingredients"),
    cuisine_type: Optional[str] = Query(None, description="Cuisine type filter"),
    meal_type: Optional[str] = Query(None, description="Meal type filter"),
    difficulty_level: Optional[str] = Query(None, description="Difficulty level filter"),
    max_prep_time: Optional[int] = Query(None, description="Maximum prep time in minutes"),
    max_cook_time: Optional[int] = Query(None, description="Maximum cook time in minutes"),
    is_vegetarian: Optional[bool] = Query(None, description="Vegetarian filter"),
    is_vegan: Optional[bool] = Query(None, description="Vegan filter"),
    is_gluten_free: Optional[bool] = Query(None, description="Gluten-free filter"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating filter"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Advanced recipe search with multiple filters
    
    - **query**: Search in recipe titles and descriptions
    - **ingredients**: Find recipes containing specific ingredients (comma-separated)
    - **cuisine_type**: Filter by cuisine (italian, mexican, chinese, etc.)
    - **meal_type**: Filter by meal type (breakfast, lunch, dinner, etc.)
    - **difficulty_level**: Filter by difficulty (easy, medium, hard)
    - **max_prep_time**: Maximum preparation time in minutes
    - **max_cook_time**: Maximum cooking time in minutes
    - **is_vegetarian**: Show only vegetarian recipes
    - **is_vegan**: Show only vegan recipes
    - **is_gluten_free**: Show only gluten-free recipes
    - **min_rating**: Minimum average rating (0-5)
    """
    
    service = SearchService(db)
    
    # Parse ingredients
    ingredient_list = []
    if ingredients:
        ingredient_list = [ing.strip() for ing in ingredients.split(',') if ing.strip()]
    
    search_filters = {
        "query": query,
        "ingredients": ingredient_list,
        "cuisine_type": cuisine_type,
        "meal_type": meal_type,
        "difficulty_level": difficulty_level,
        "max_prep_time": max_prep_time,
        "max_cook_time": max_cook_time,
        "is_vegetarian": is_vegetarian,
        "is_vegan": is_vegan,
        "is_gluten_free": is_gluten_free,
        "min_rating": min_rating
    }
    
    return service.search_recipes(
        filters=search_filters,
        page=page,
        limit=limit,
        user_id=current_user.id if current_user else None
    )

@router.get("/ingredients", response_model=List[IngredientResponse])
async def search_ingredients(
    query: str = Query(..., min_length=1, description="Ingredient search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """Search ingredients by name"""
    
    service = SearchService(db)
    return service.search_ingredients(query, limit)

@router.get("/autocomplete")
async def autocomplete_search(
    query: str = Query(..., min_length=1, description="Search query for autocomplete"),
    db: Session = Depends(get_db)
):
    """Get search autocomplete suggestions"""
    
    service = SearchService(db)
    return service.get_autocomplete_suggestions(query)

@router.get("/popular")
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=20, description="Number of popular searches to return"),
    db: Session = Depends(get_db)
):
    """Get popular search terms"""
    
    service = SearchService(db)
    return service.get_popular_searches(limit)

@router.get("/trending")
async def get_trending_recipes(
    limit: int = Query(10, ge=1, le=50, description="Number of trending recipes"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get trending recipes based on recent views and ratings"""
    
    service = SearchService(db)
    return service.get_trending_recipes(
        limit=limit,
        user_id=current_user.id if current_user else None
    )