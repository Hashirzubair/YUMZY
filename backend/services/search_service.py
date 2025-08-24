from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, ilike

from models.recipe import Recipe
from models.ingredient import Ingredient
from models.user import User
from models.recipe_ingredient import RecipeIngredient
from schemas.search import SearchResponse, IngredientResponse
from schemas.recipe import RecipeResponse
import logging

logger = logging.getLogger(__name__)

class SearchService:
    """Service class for search-related functionality"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search_recipes(
        self, 
        filters: Dict[str, Any],
        page: int = 1,
        limit: int = 20,
        user_id: Optional[int] = None
    ) -> SearchResponse:
        """Advanced recipe search with filters"""
        
        offset = (page - 1) * limit
        query = self.db.query(Recipe).filter(Recipe.is_published == True)
        
        # Text search in title and description
        if filters.get('query'):
            search_term = f"%{filters['query']}%"
            query = query.filter(
                or_(
                    Recipe.title.ilike(search_term),
                    Recipe.description.ilike(search_term)
                )
            )
        
        # Ingredient-based search
        if filters.get('ingredients'):
            ingredient_names = filters['ingredients']
            # Find recipes that contain any of the specified ingredients
            ingredient_ids = self.db.query(Ingredient.id).filter(
                Ingredient.name.in_(ingredient_names)
            ).subquery()
            
            recipe_ids = self.db.query(RecipeIngredient.recipe_id).filter(
                RecipeIngredient.ingredient_id.in_(ingredient_ids)
            ).subquery()
            
            query = query.filter(Recipe.id.in_(recipe_ids))
        
        # Apply other filters
        if filters.get('cuisine_type'):
            query = query.filter(Recipe.cuisine_type == filters['cuisine_type'])
        
        if filters.get('meal_type'):
            query = query.filter(Recipe.meal_type == filters['meal_type'])
        
        if filters.get('difficulty_level'):
            query = query.filter(Recipe.difficulty_level == filters['difficulty_level'])
        
        if filters.get('max_prep_time'):
            query = query.filter(Recipe.prep_time <= filters['max_prep_time'])
        
        if filters.get('max_cook_time'):
            query = query.filter(Recipe.cook_time <= filters['max_cook_time'])
        
        if filters.get('is_vegetarian'):
            query = query.filter(Recipe.is_vegetarian == filters['is_vegetarian'])
        
        if filters.get('is_vegan'):
            query = query.filter(Recipe.is_vegan == filters['is_vegan'])
        
        if filters.get('is_gluten_free'):
            query = query.filter(Recipe.is_gluten_free == filters['is_gluten_free'])
        
        if filters.get('min_rating'):
            query = query.filter(Recipe.average_rating >= filters['min_rating'])
        
        # Get total count
        total_count = query.count()
        
        # Apply sorting - default by relevance (view count + rating)
        if filters.get('query') or filters.get('ingredients'):
            # For search queries, sort by relevance
            query = query.order_by(
                desc(Recipe.average_rating * Recipe.rating_count + Recipe.view_count)
            )
        else:
            # For browsing, sort by creation date
            query = query.order_by(desc(Recipe.created_at))
        
        # Get recipes with pagination
        recipes = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        recipe_responses = []
        for recipe in recipes:
            recipe_response = self._recipe_to_response(recipe, user_id)
            recipe_responses.append(recipe_response)
        
        total_pages = (total_count + limit - 1) // limit
        
        return SearchResponse(
            recipes=recipe_responses,
            total_count=total_count,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            filters=filters
        )
    
    def search_ingredients(self, query: str, limit: int = 10) -> List[IngredientResponse]:
        """Search ingredients by name"""
        
        search_term = f"%{query}%"
        ingredients = self.db.query(Ingredient).filter(
            Ingredient.name.ilike(search_term)
        ).order_by(Ingredient.name).limit(limit).all()
        
        return [
            IngredientResponse(
                id=ingredient.id,
                name=ingredient.name,
                category=ingredient.category
            )
            for ingredient in ingredients
        ]
    
    def get_autocomplete_suggestions(self, query: str) -> Dict[str, List[str]]:
        """Get search autocomplete suggestions"""
        
        search_term = f"%{query}%"
        limit = 5
        
        # Recipe title suggestions
        recipe_titles = self.db.query(Recipe.title).filter(
            Recipe.title.ilike(search_term),
            Recipe.is_published == True
        ).distinct().limit(limit).all()
        
        # Ingredient suggestions
        ingredients = self.db.query(Ingredient.name).filter(
            Ingredient.name.ilike(search_term)
        ).distinct().limit(limit).all()
        
        # Cuisine suggestions
        cuisines = self.db.query(Recipe.cuisine_type).filter(
            Recipe.cuisine_type.ilike(search_term),
            Recipe.cuisine_type.isnot(None),
            Recipe.is_published == True
        ).distinct().limit(limit).all()
        
        return {
            "recipes": [title[0] for title in recipe_titles],
            "ingredients": [ingredient[0] for ingredient in ingredients],
            "cuisines": [cuisine[0] for cuisine in cuisines]
        }
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular search terms (simulated for now)"""
        
        # In a real app, this would be based on search analytics
        # For now, return most popular cuisines and ingredients
        
        popular_cuisines = self.db.query(
            Recipe.cuisine_type,
            func.count(Recipe.id).label('count')
        ).filter(
            Recipe.cuisine_type.isnot(None),
            Recipe.is_published == True
        ).group_by(Recipe.cuisine_type).order_by(
            desc('count')
        ).limit(limit // 2).all()
        
        popular_ingredients = self.db.query(
            Ingredient.name,
            func.count(RecipeIngredient.recipe_id).label('count')
        ).join(RecipeIngredient).group_by(
            Ingredient.name
        ).order_by(desc('count')).limit(limit // 2).all()
        
        results = []
        
        for cuisine, count in popular_cuisines:
            results.append({
                "term": cuisine,
                "type": "cuisine",
                "count": count
            })
        
        for ingredient, count in popular_ingredients:
            results.append({
                "term": ingredient,
                "type": "ingredient",
                "count": count
            })
        
        return sorted(results, key=lambda x: x['count'], reverse=True)[:limit]
    
    def get_trending_recipes(self, limit: int = 10, user_id: Optional[int] = None) -> List[RecipeResponse]:
        """Get trending recipes based on recent activity"""
        
        from datetime import datetime, timedelta
        
        # Get recipes with high recent activity (views in last 7 days)
        recent_date = datetime.utcnow() - timedelta(days=7)
        
        # For simplicity, we'll use recipes with highest combined score
        # In a real app, you'd track daily/weekly view counts
        trending_recipes = self.db.query(Recipe).filter(
            Recipe.is_published == True,
            Recipe.created_at >= recent_date - timedelta(days=30)  # Created in last 30 days
        ).order_by(
            desc(Recipe.view_count + Recipe.favorite_count * 2 + Recipe.rating_count * 3)
        ).limit(limit).all()
        
        return [self._recipe_to_response(recipe, user_id) for recipe in trending_recipes]
    
    def search_by_ingredients_advanced(
        self, 
        have_ingredients: List[str], 
        avoid_ingredients: List[str] = None,
        limit: int = 20
    ) -> List[RecipeResponse]:
        """Advanced ingredient-based search"""
        
        # Find ingredient IDs
        have_ids = []
        if have_ingredients:
            have_ids = [
                ing.id for ing in self.db.query(Ingredient).filter(
                    Ingredient.name.in_(have_ingredients)
                ).all()
            ]
        
        avoid_ids = []
        if avoid_ingredients:
            avoid_ids = [
                ing.id for ing in self.db.query(Ingredient).filter(
                    Ingredient.name.in_(avoid_ingredients)
                ).all()
            ]
        
        # Find recipes with desired ingredients
        if have_ids:
            recipe_ids_with_ingredients = self.db.query(RecipeIngredient.recipe_id).filter(
                RecipeIngredient.ingredient_id.in_(have_ids)
            ).distinct().subquery()
        else:
            recipe_ids_with_ingredients = self.db.query(Recipe.id).subquery()
        
        # Exclude recipes with avoided ingredients
        if avoid_ids:
            recipe_ids_to_avoid = self.db.query(RecipeIngredient.recipe_id).filter(
                RecipeIngredient.ingredient_id.in_(avoid_ids)
            ).distinct().subquery()
            
            recipes = self.db.query(Recipe).filter(
                Recipe.id.in_(recipe_ids_with_ingredients),
                Recipe.id.notin_(recipe_ids_to_avoid),
                Recipe.is_published == True
            ).order_by(desc(Recipe.average_rating)).limit(limit).all()
        else:
            recipes = self.db.query(Recipe).filter(
                Recipe.id.in_(recipe_ids_with_ingredients),
                Recipe.is_published == True
            ).order_by(desc(Recipe.average_rating)).limit(limit).all()
        
        return [self._recipe_to_response(recipe) for recipe in recipes]
    
    def _recipe_to_response(self, recipe: Recipe, user_id: Optional[int] = None) -> RecipeResponse:
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
        
        # User-specific data
        is_favorited = False
        user_rating = None
        
        if user_id:
            recipe_service = RecipeService(self.db)
            is_favorited = recipe_service.is_recipe_favorited(recipe.id, user_id)
            rating = recipe_service.get_user_rating(recipe.id, user_id)
            user_rating = rating.rating if rating else None
        
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
            ingredients=ingredients,
            is_favorited=is_favorited,
            user_rating=user_rating
        )