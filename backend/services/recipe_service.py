from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta

from models.recipe import Recipe
from models.ingredient import Ingredient
from models.user import User
from models.rating import Rating
from models.favorite import Favorite
from models.recipe_ingredient import RecipeIngredient
from schemas.recipe import RecipeResponse, RecipeDetailed, RecipeListResponse, RecipeCreate, RecipeUpdate
from schemas.favorite import FavoriteResponse
from schemas.rating import RatingCreate, RatingResponse
from core.exceptions import RecipeNotFoundError, RecipeAccessDeniedError
import logging

logger = logging.getLogger(__name__)

class RecipeService:
    """Service class for recipe-related business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_recipes(
        self, 
        page: int = 1, 
        limit: int = 20, 
        filters: Dict[str, Any] = None,
        user_id: Optional[int] = None
    ) -> RecipeListResponse:
        """Get recipes with filters and pagination"""
        
        offset = (page - 1) * limit
        query = self.db.query(Recipe).filter(Recipe.is_published == True)
        
        # Apply filters
        if filters:
            if filters.get('cuisine_type'):
                query = query.filter(Recipe.cuisine_type == filters['cuisine_type'])
            if filters.get('meal_type'):
                query = query.filter(Recipe.meal_type == filters['meal_type'])
            if filters.get('difficulty_level'):
                query = query.filter(Recipe.difficulty_level == filters['difficulty_level'])
            if filters.get('max_prep_time'):
                query = query.filter(Recipe.prep_time <= filters['max_prep_time'])
            if filters.get('is_vegetarian'):
                query = query.filter(Recipe.is_vegetarian == filters['is_vegetarian'])
            if filters.get('is_vegan'):
                query = query.filter(Recipe.is_vegan == filters['is_vegan'])
            if filters.get('is_gluten_free'):
                query = query.filter(Recipe.is_gluten_free == filters['is_gluten_free'])
        
        # Get total count
        total_count = query.count()
        
        # Get recipes with pagination
        recipes = query.order_by(desc(Recipe.created_at)).offset(offset).limit(limit).all()
        
        # Convert to response format
        recipe_responses = []
        for recipe in recipes:
            recipe_response = self._recipe_to_response(recipe)
            
            # Add user-specific data if user is authenticated
            if user_id:
                recipe_response.is_favorited = self.is_recipe_favorited(recipe.id, user_id)
                user_rating = self.get_user_rating(recipe.id, user_id)
                recipe_response.user_rating = user_rating.rating if user_rating else None
            
            recipe_responses.append(recipe_response)
        
        total_pages = (total_count + limit - 1) // limit
        
        return RecipeListResponse(
            recipes=recipe_responses,
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    
    def create_recipe(self, recipe_data: RecipeCreate, user_id: int) -> RecipeResponse:
        """Create a new recipe"""
        
        # Calculate total time
        total_time = (recipe_data.prep_time or 0) + (recipe_data.cook_time or 0)
        
        # Create recipe
        recipe = Recipe(
            title=recipe_data.title,
            description=recipe_data.description,
            instructions=recipe_data.instructions,
            prep_time=recipe_data.prep_time,
            cook_time=recipe_data.cook_time,
            total_time=total_time,
            servings=recipe_data.servings,
            difficulty_level=recipe_data.difficulty_level,
            cuisine_type=recipe_data.cuisine_type,
            meal_type=recipe_data.meal_type,
            author_id=user_id
        )
        
        self.db.add(recipe)
        self.db.flush()  # Get recipe ID
        
        # Add ingredients
        if recipe_data.ingredients:
            for ingredient_data in recipe_data.ingredients:
                # Find or create ingredient
                ingredient = self.db.query(Ingredient).filter(
                    Ingredient.name.ilike(ingredient_data.name)
                ).first()
                
                if not ingredient:
                    ingredient = Ingredient(
                        name=ingredient_data.name,
                        category=ingredient_data.category
                    )
                    self.db.add(ingredient)
                    self.db.flush()
                
                # Create recipe-ingredient relationship
                recipe_ingredient = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ingredient.id,
                    quantity=ingredient_data.quantity,
                    unit=ingredient_data.unit
                )
                self.db.add(recipe_ingredient)
        
        self.db.commit()
        self.db.refresh(recipe)
        
        logger.info(f"Recipe created: {recipe.id} by user {user_id}")
        return self._recipe_to_response(recipe)
    
    def get_recipe_detailed(self, recipe_id: int, user_id: Optional[int] = None) -> RecipeDetailed:
        """Get detailed recipe information"""
        
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            raise RecipeNotFoundError()
        
        # Check if user can view private recipe
        if not recipe.is_published and recipe.author_id != user_id:
            raise RecipeAccessDeniedError()
        
        # Get user-specific data
        user_rating = None
        is_favorited = False
        
        if user_id:
            user_rating_obj = self.get_user_rating(recipe_id, user_id)
            user_rating = user_rating_obj.rating if user_rating_obj else None
            is_favorited = self.is_recipe_favorited(recipe_id, user_id)
        
        # Get similar recipes
        similar_recipes = self.get_similar_recipes(recipe_id, limit=5)
        
        recipe_response = self._recipe_to_response(recipe)
        
        return RecipeDetailed(
            **recipe_response.dict(),
            user_rating=user_rating,
            is_favorited=is_favorited,
            similar_recipes=similar_recipes
        )
    
    def update_recipe(self, recipe_id: int, recipe_update: RecipeUpdate, user_id: int) -> RecipeResponse:
        """Update recipe (only by author)"""
        
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            raise RecipeNotFoundError()
        
        if recipe.author_id != user_id:
            raise RecipeAccessDeniedError("Not authorized to update this recipe")
        
        # Update fields
        update_data = recipe_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(recipe, field, value)
        
        # Recalculate total time if needed
        if 'prep_time' in update_data or 'cook_time' in update_data:
            recipe.total_time = (recipe.prep_time or 0) + (recipe.cook_time or 0)
        
        self.db.commit()
        self.db.refresh(recipe)
        
        logger.info(f"Recipe updated: {recipe_id} by user {user_id}")
        return self._recipe_to_response(recipe)
    
    def delete_recipe(self, recipe_id: int, user_id: int) -> None:
        """Delete recipe (only by author)"""
        
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            raise RecipeNotFoundError()
        
        if recipe.author_id != user_id:
            raise RecipeAccessDeniedError("Not authorized to delete this recipe")
        
        self.db.delete(recipe)
        self.db.commit()
        
        logger.info(f"Recipe deleted: {recipe_id} by user {user_id}")
    
    def get_user_recipes(self, user_id: int, page: int = 1, limit: int = 20) -> List[RecipeResponse]:
        """Get recipes created by a user"""
        
        offset = (page - 1) * limit
        
        recipes = self.db.query(Recipe).filter(
            Recipe.author_id == user_id,
            Recipe.is_published == True
        ).order_by(desc(Recipe.created_at)).offset(offset).limit(limit).all()
        
        return [self._recipe_to_response(recipe) for recipe in recipes]
    
    def get_similar_recipes(self, recipe_id: int, limit: int = 5) -> List[RecipeResponse]:
        """Get recipes similar to the given recipe"""
        
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            return []
        
        # Simple similarity based on cuisine and meal type
        similar_recipes = self.db.query(Recipe).filter(
            Recipe.id != recipe_id,
            Recipe.is_published == True,
            or_(
                Recipe.cuisine_type == recipe.cuisine_type,
                Recipe.meal_type == recipe.meal_type
            )
        ).order_by(desc(Recipe.average_rating)).limit(limit).all()
        
        return [self._recipe_to_response(r) for r in similar_recipes]
    
    def track_recipe_view(self, recipe_id: int, user_id: Optional[int] = None):
        """Track recipe view for analytics"""
        
        try:
            recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
            if recipe:
                recipe.view_count = (recipe.view_count or 0) + 1
                self.db.commit()
        except Exception as e:
            logger.error(f"Error tracking recipe view: {str(e)}")
    
    # Favorites Management
    def add_to_favorites(self, recipe_id: int, user_id: int, notes: Optional[str] = None) -> FavoriteResponse:
        """Add recipe to user favorites"""
        
        # Check if recipe exists
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            raise RecipeNotFoundError()
        
        # Check if already favorited
        if self.is_recipe_favorited(recipe_id, user_id):
            raise ValueError("Recipe already in favorites")
        
        favorite = Favorite(
            recipe_id=recipe_id,
            user_id=user_id,
            notes=notes
        )
        self.db.add(favorite)
        
        # Update recipe favorite count
        recipe.favorite_count = (recipe.favorite_count or 0) + 1
        
        self.db.commit()
        self.db.refresh(favorite)
        
        return FavoriteResponse(
            id=favorite.id,
            recipe_id=recipe_id,
            recipe_title=recipe.title,
            recipe_image=recipe.main_image,
            notes=notes,
            created_at=favorite.created_at
        )
    
    def remove_from_favorites(self, recipe_id: int, user_id: int) -> None:
        """Remove recipe from user favorites"""
        
        favorite = self.db.query(Favorite).filter(
            and_(Favorite.recipe_id == recipe_id, Favorite.user_id == user_id)
        ).first()
        
        if not favorite:
            raise ValueError("Recipe not in favorites")
        
        self.db.delete(favorite)
        
        # Update recipe favorite count
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if recipe:
            recipe.favorite_count = max(0, (recipe.favorite_count or 0) - 1)
        
        self.db.commit()
    
    def is_recipe_favorited(self, recipe_id: int, user_id: int) -> bool:
        """Check if recipe is favorited by user"""
        
        favorite = self.db.query(Favorite).filter(
            and_(Favorite.recipe_id == recipe_id, Favorite.user_id == user_id)
        ).first()
        
        return favorite is not None
    
    def get_user_favorites(self, user_id: int, page: int = 1, limit: int = 20) -> List[FavoriteResponse]:
        """Get user's favorite recipes"""
        
        offset = (page - 1) * limit
        
        favorites = self.db.query(Favorite).join(Recipe).filter(
            Favorite.user_id == user_id,
            Recipe.is_published == True
        ).order_by(desc(Favorite.created_at)).offset(offset).limit(limit).all()
        
        return [
            FavoriteResponse(
                id=fav.id,
                recipe_id=fav.recipe_id,
                recipe_title=fav.recipe.title,
                recipe_image=fav.recipe.main_image,
                notes=fav.notes,
                created_at=fav.created_at
            )
            for fav in favorites
        ]
    
    # Rating System
    def create_rating(self, rating_data: RatingCreate, user_id: int) -> RatingResponse:
        """Create or update recipe rating"""
        
        # Check if recipe exists
        recipe = self.db.query(Recipe).filter(Recipe.id == rating_data.recipe_id).first()
        if not recipe:
            raise RecipeNotFoundError()
        
        # Check for existing rating
        existing_rating = self.db.query(Rating).filter(
            and_(Rating.recipe_id == rating_data.recipe_id, Rating.user_id == user_id)
        ).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating_data.rating
            existing_rating.comment = rating_data.comment
            rating_obj = existing_rating
        else:
            # Create new rating
            rating_obj = Rating(
                rating=rating_data.rating,
                comment=rating_data.comment,
                user_id=user_id,
                recipe_id=rating_data.recipe_id
            )
            self.db.add(rating_obj)
        
        self.db.flush()
        
        # Recalculate recipe average rating
        avg_rating = self.db.query(func.avg(Rating.rating)).filter(
            Rating.recipe_id == rating_data.recipe_id
        ).scalar()
        
        rating_count = self.db.query(func.count(Rating.id)).filter(
            Rating.recipe_id == rating_data.recipe_id
        ).scalar()
        
        recipe.average_rating = float(avg_rating) if avg_rating else 0.0
        recipe.rating_count = rating_count
        
        self.db.commit()
        self.db.refresh(rating_obj)
        
        return RatingResponse(
            id=rating_obj.id,
            rating=rating_obj.rating,
            comment=rating_obj.comment,
            user_id=user_id,
            recipe_id=rating_data.recipe_id,
            created_at=rating_obj.created_at,
            updated_at=rating_obj.updated_at
        )
    
    def get_user_rating(self, recipe_id: int, user_id: int) -> Optional[Rating]:
        """Get user's rating for a recipe"""
        
        return self.db.query(Rating).filter(
            and_(Rating.recipe_id == recipe_id, Rating.user_id == user_id)
        ).first()
    
    def get_recipe_ratings(self, recipe_id: int, page: int = 1, limit: int = 20) -> List[RatingResponse]:
        """Get ratings for a recipe"""
        
        offset = (page - 1) * limit
        
        ratings = self.db.query(Rating).join(User).filter(
            Rating.recipe_id == recipe_id
        ).order_by(desc(Rating.created_at)).offset(offset).limit(limit).all()
        
        return [
            RatingResponse(
                id=rating.id,
                rating=rating.rating,
                comment=rating.comment,
                user_id=rating.user_id,
                recipe_id=recipe_id,
                username=rating.user.username,
                created_at=rating.created_at,
                updated_at=rating.updated_at
            )
            for rating in ratings
        ]
    
    def get_share_url(self, recipe_id: int, platform: str = "general") -> dict:
        """Get shareable URL for recipe"""
        
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            raise RecipeNotFoundError()
        
        base_url = "https://yumzy.app"  # Replace with your actual domain
        share_url = f"{base_url}/recipes/{recipe_id}"
        
        return {
            "recipe_id": recipe_id,
            "recipe_title": recipe.title,
            "share_url": share_url,
            "platform": platform
        }
    
    def track_recipe_share(self, recipe_id: int, platform: str, user_id: int) -> dict:
        """Track recipe share"""
        
        # This would typically store share tracking data
        # For simplicity, we'll just return confirmation
        
        logger.info(f"Recipe {recipe_id} shared on {platform} by user {user_id}")
        
        return {
            "recipe_id": recipe_id,
            "platform": platform,
            "shared_at": datetime.utcnow(),
            "success": True
        }
    
    # Utility Methods
    def _recipe_to_response(self, recipe: Recipe) -> RecipeResponse:
        """Convert recipe model to response schema"""
        
        # Get ingredients
        ingredients = []
        recipe_ingredients = self.db.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == recipe.id
        ).all()
        
        for ri in recipe_ingredients:
            ingredient = self.db.query(Ingredient).filter(
                Ingredient.id == ri.ingredient_id
            ).first()
            if ingredient:
                ingredients.append({
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "quantity": ri.quantity,
                    "unit": ri.unit,
                    "category": ingredient.category
                })
        
        return RecipeResponse(
            id=recipe.id,
            title=recipe.title,
            description=recipe.description,
            instructions=recipe.instructions,
            prep_time=recipe.prep_time,
            cook_time=recipe.cook_time,
            total_time=recipe.total_time,
            servings=recipe.servings,
            difficulty_level=recipe.difficulty_level,
            cuisine_type=recipe.cuisine_type,
            meal_type=recipe.meal_type,
            is_vegetarian=recipe.is_vegetarian or False,
            is_vegan=recipe.is_vegan or False,
            is_gluten_free=recipe.is_gluten_free or False,
            main_image=recipe.main_image,
            average_rating=recipe.average_rating or 0.0,
            rating_count=recipe.rating_count or 0,
            view_count=recipe.view_count or 0,
            favorite_count=recipe.favorite_count or 0,
            created_at=recipe.created_at,
            author_id=recipe.author_id,
            author_username=recipe.author.username if recipe.author else None,
            ingredients=ingredients
        )