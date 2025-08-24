from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models.recipe import Recipe
from models.user import User
from models.favorite import Favorite
from models.rating import Rating
from schemas.recipe import RecipeResponse
import logging
import random

logger = logging.getLogger(__name__)

class RecommendationService:
    """Service class for AI-powered recipe recommendations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_personalized_recommendations(
        self, 
        user_id: int, 
        limit: int = 10,
        exclude_recipe_ids: List[int] = None
    ) -> List[RecipeResponse]:
        """Get personalized recipe recommendations for user"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        exclude_ids = exclude_recipe_ids or []
        
        # Get user's favorite cuisines
        favorite_cuisines = self._get_user_favorite_cuisines(user_id)
        
        # Get user's dietary preferences
        dietary_filters = self._get_dietary_filters(user)
        
        # Build recommendation query
        query = self.db.query(Recipe).filter(
            Recipe.is_published == True,
            Recipe.id.notin_(exclude_ids)
        )
        
        # Apply dietary filters
        for filter_name, filter_value in dietary_filters.items():
            if filter_value:
                query = query.filter(getattr(Recipe, filter_name) == True)
        
        # Prefer recipes from favorite cuisines
        if favorite_cuisines:
            cuisine_recipes = query.filter(
                Recipe.cuisine_type.in_(favorite_cuisines)
            ).order_by(desc(Recipe.average_rating)).limit(limit // 2).all()
            
            # Get additional recipes from other cuisines
            other_recipes = query.filter(
                Recipe.cuisine_type.notin_(favorite_cuisines)
            ).order_by(desc(Recipe.average_rating)).limit(limit - len(cuisine_recipes)).all()
            
            recommended_recipes = cuisine_recipes + other_recipes
        else:
            # No cuisine preferences, recommend highly rated recipes
            recommended_recipes = query.order_by(
                desc(Recipe.average_rating)
            ).limit(limit).all()
        
        return [self._recipe_to_response(recipe) for recipe in recommended_recipes[:limit]]
    
    def get_similar_recipes(
        self, 
        recipe_id: int, 
        limit: int = 5,
        exclude_recipe_ids: List[int] = None
    ) -> List[RecipeResponse]:
        """Get recipes similar to the specified recipe"""
        
        recipe = self.db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            return []
        
        exclude_ids = (exclude_recipe_ids or []) + [recipe_id]
        
        # Find similar recipes based on cuisine, meal type, and ingredients
        similar_recipes = self.db.query(Recipe).filter(
            Recipe.is_published == True,
            Recipe.id.notin_(exclude_ids),
            Recipe.cuisine_type == recipe.cuisine_type,
            Recipe.meal_type == recipe.meal_type
        ).order_by(desc(Recipe.average_rating)).limit(limit).all()
        
        # If not enough similar recipes, broaden search
        if len(similar_recipes) < limit:
            additional_recipes = self.db.query(Recipe).filter(
                Recipe.is_published == True,
                Recipe.id.notin_(exclude_ids + [r.id for r in similar_recipes]),
                Recipe.cuisine_type == recipe.cuisine_type
            ).order_by(desc(Recipe.average_rating)).limit(limit - len(similar_recipes)).all()
            
            similar_recipes.extend(additional_recipes)
        
        return [self._recipe_to_response(recipe) for recipe in similar_recipes[:limit]]
    
    def get_trending_recommendations(self, limit: int = 10, user_id: Optional[int] = None) -> List[RecipeResponse]:
        """Get trending recipe recommendations"""
        
        # Get recipes with high recent activity
        trending_recipes = self.db.query(Recipe).filter(
            Recipe.is_published == True
        ).order_by(
            desc(Recipe.view_count + Recipe.favorite_count * 2 + Recipe.rating_count * 3)
        ).limit(limit * 2).all()  # Get more to allow for filtering
        
        # If user is provided, apply their dietary preferences
        if user_id:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                dietary_filters = self._get_dietary_filters(user)
                filtered_recipes = []
                
                for recipe in trending_recipes:
                    is_suitable = True
                    for filter_name, filter_value in dietary_filters.items():
                        if filter_value and not getattr(recipe, filter_name, False):
                            is_suitable = False
                            break
                    
                    if is_suitable:
                        filtered_recipes.append(recipe)
                    
                    if len(filtered_recipes) >= limit:
                        break
                
                trending_recipes = filtered_recipes
        
        return [self._recipe_to_response(recipe) for recipe in trending_recipes[:limit]]
    
    def get_cuisine_based_recommendations(
        self, 
        cuisine_type: str, 
        limit: int = 10,
        exclude_recipe_ids: List[int] = None
    ) -> List[RecipeResponse]:
        """Get recommendations based on specific cuisine"""
        
        exclude_ids = exclude_recipe_ids or []
        
        recipes = self.db.query(Recipe).filter(
            Recipe.is_published == True,
            Recipe.cuisine_type == cuisine_type,
            Recipe.id.notin_(exclude_ids)
        ).order_by(desc(Recipe.average_rating)).limit(limit).all()
        
        return [self._recipe_to_response(recipe) for recipe in recipes]
    
    def get_random_recommendations(self, limit: int = 10, user_id: Optional[int] = None) -> List[RecipeResponse]:
        """Get random recipe recommendations"""
        
        # Get total count of published recipes
        total_recipes = self.db.query(func.count(Recipe.id)).filter(
            Recipe.is_published == True
        ).scalar()
        
        if total_recipes == 0:
            return []
        
        # Generate random offsets
        random_offsets = random.sample(range(total_recipes), min(limit * 3, total_recipes))
        
        random_recipes = []
        for offset in random_offsets[:limit]:
            recipe = self.db.query(Recipe).filter(
                Recipe.is_published == True
            ).offset(offset).limit(1).first()
            
            if recipe:
                # Apply user dietary preferences if provided
                if user_id:
                    user = self.db.query(User).filter(User.id == user_id).first()
                    if user:
                        dietary_filters = self._get_dietary_filters(user)
                        is_suitable = True
                        
                        for filter_name, filter_value in dietary_filters.items():
                            if filter_value and not getattr(recipe, filter_name, False):
                                is_suitable = False
                                break
                        
                        if is_suitable:
                            random_recipes.append(recipe)
                else:
                    random_recipes.append(recipe)
            
            if len(random_recipes) >= limit:
                break
        
        return [self._recipe_to_response(recipe) for recipe in random_recipes]
    
    def get_quick_meal_recommendations(self, max_prep_time: int = 30, limit: int = 10) -> List[RecipeResponse]:
        """Get recommendations for quick meals"""
        
        quick_recipes = self.db.query(Recipe).filter(
            Recipe.is_published == True,
            Recipe.prep_time <= max_prep_time
        ).order_by(desc(Recipe.average_rating)).limit(limit).all()
        
        return [self._recipe_to_response(recipe) for recipe in quick_recipes]
    
    def _get_user_favorite_cuisines(self, user_id: int, limit: int = 5) -> List[str]:
        """Get user's favorite cuisines based on their favorites and ratings"""
        
        # Get cuisines from user's favorite recipes
        favorite_cuisines = self.db.query(
            Recipe.cuisine_type,
            func.count(Recipe.cuisine_type).label('count')
        ).join(Favorite).filter(
            Favorite.user_id == user_id,
            Recipe.cuisine_type.isnot(None)
        ).group_by(Recipe.cuisine_type).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [cuisine for cuisine, _ in favorite_cuisines]
    
    def _get_dietary_filters(self, user: User) -> Dict[str, bool]:
        """Get dietary filters for user"""
        
        return {
            'is_vegetarian': user.is_vegetarian or False,
            'is_vegan': user.is_vegan or False,
            'is_gluten_free': user.is_gluten_free or False
        }
    
    def _recipe_to_response(self, recipe: Recipe) -> RecipeResponse:
        """Convert recipe model to response schema"""
        
        from services.recipe_service import RecipeService
        
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