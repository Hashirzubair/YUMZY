from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from core.security import get_current_user
from models.user import User
from services.shopping_service import ShoppingService
from schemas.shopping import (
    ShoppingListCreate, ShoppingListResponse, ShoppingListItemCreate,
    ShoppingListItemResponse, ShoppingListUpdate
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/shopping-lists", tags=["Shopping Lists"])

@router.get("", response_model=List[ShoppingListResponse])
async def get_shopping_lists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's shopping lists"""
    
    service = ShoppingService(db)
    return service.get_user_shopping_lists(current_user.id)

@router.post("", response_model=ShoppingListResponse, status_code=status.HTTP_201_CREATED)
async def create_shopping_list(
    list_data: ShoppingListCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new shopping list"""
    
    service = ShoppingService(db)
    return service.create_shopping_list(list_data, current_user.id)

@router.get("/{list_id}", response_model=ShoppingListResponse)
async def get_shopping_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific shopping list"""
    
    service = ShoppingService(db)
    return service.get_shopping_list(list_id, current_user.id)

@router.put("/{list_id}", response_model=ShoppingListResponse)
async def update_shopping_list(
    list_id: int,
    list_update: ShoppingListUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update shopping list"""
    
    service = ShoppingService(db)
    return service.update_shopping_list(list_id, list_update, current_user.id)

@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shopping_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete shopping list"""
    
    service = ShoppingService(db)
    service.delete_shopping_list(list_id, current_user.id)

@router.post("/{list_id}/items", response_model=ShoppingListItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_list(
    list_id: int,
    item_data: ShoppingListItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add item to shopping list"""
    
    service = ShoppingService(db)
    return service.add_item_to_list(list_id, item_data, current_user.id)

@router.put("/{list_id}/items/{item_id}")
async def update_list_item(
    list_id: int,
    item_id: int,
    item_update: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update shopping list item"""
    
    service = ShoppingService(db)
    return service.update_list_item(list_id, item_id, item_update, current_user.id)

@router.delete("/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_list(
    list_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove item from shopping list"""
    
    service = ShoppingService(db)
    service.remove_item_from_list(list_id, item_id, current_user.id)

@router.post("/from-recipe/{recipe_id}", response_model=ShoppingListResponse, status_code=status.HTTP_201_CREATED)
async def create_list_from_recipe(
    recipe_id: int,
    list_name: str = "Shopping List",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create shopping list from recipe ingredients"""
    
    service = ShoppingService(db)
    return service.create_list_from_recipe(recipe_id, list_name, current_user.id)

@router.post("/{list_id}/toggle/{item_id}")
async def toggle_item_purchased(
    list_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle item purchased status"""
    
    service = ShoppingService(db)
    return service.toggle_item_purchased(list_id, item_id, current_user.id)