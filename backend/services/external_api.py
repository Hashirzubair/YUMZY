import requests
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ExternalAPIService:
    """Service for integrating with external recipe APIs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search_spoonacular_recipes(
        self, 
        query: str, 
        cuisine: Optional[str] = None,
        diet: Optional[str] = None,
        number: int = 10
    ) -> List[Dict[str, Any]]:
        """Search recipes from Spoonacular API (if API key available)"""
        
        # This is a placeholder implementation
        # In real implementation, you would:
        # 1. Get API key from environment variables
        # 2. Make HTTP request to Spoonacular API
        # 3. Parse and return results
        
        logger.info(f"External API search for: {query}")
        
        # Simulated response structure
        sample_recipes = [
            {
                "id": 1001,
                "title": f"External Recipe: {query}",
                "image": "https://example.com/image1.jpg",
                "readyInMinutes": 30,
                "servings": 4,
                "sourceUrl": "https://example.com/recipe1",
                "summary": f"A delicious recipe for {query}",
                "cuisines": [cuisine] if cuisine else ["international"],
                "diets": [diet] if diet else [],
                "vegan": diet == "vegan",
                "vegetarian": diet in ["vegetarian", "vegan"],
                "glutenFree": diet == "gluten free"
            }
        ]
        
        return sample_recipes
    
    def get_recipe_nutrition(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """Get nutrition information for a recipe"""
        
        # Placeholder for nutrition API integration
        return {
            "calories": 250,
            "protein": "15g",
            "carbohydrates": "30g", 
            "fat": "8g",
            "fiber": "5g",
            "sugar": "10g",
            "sodium": "400mg"
        }
    
    def import_external_recipe(self, external_recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Import recipe from external API into our database"""
        
        from models.recipe import Recipe
        from models.ingredient import Ingredient
        from models.recipe_ingredient import RecipeIngredient
        
        try:
            # Create recipe from external data
            recipe = Recipe(
                title=external_recipe.get('title'),
                description=external_recipe.get('summary', ''),
                instructions=external_recipe.get('instructions', ''),
                prep_time=external_recipe.get('readyInMinutes', 0),
                cook_time=0,  # Spoonacular doesn't separate prep/cook time
                total_time=external_recipe.get('readyInMinutes', 0),
                servings=external_recipe.get('servings', 4),
                cuisine_type=external_recipe.get('cuisines', [None])[0],
                main_image=external_recipe.get('image'),
                is_vegetarian=external_recipe.get('vegetarian', False),
                is_vegan=external_recipe.get('vegan', False),
                is_gluten_free=external_recipe.get('glutenFree', False),
                external_source='spoonacular',
                external_api_id=str(external_recipe.get('id')),
                source_url=external_recipe.get('sourceUrl'),
                author_id=1  # System user for external recipes
            )
            
            self.db.add(recipe)
            self.db.flush()
            
            # Add ingredients if available
            if 'extendedIngredients' in external_recipe:
                for ing_data in external_recipe['extendedIngredients']:
                    # Find or create ingredient
                    ingredient = self.db.query(Ingredient).filter(
                        Ingredient.name.ilike(ing_data.get('name', ''))
                    ).first()
                    
                    if not ingredient:
                        ingredient = Ingredient(
                            name=ing_data.get('name', ''),
                            category=ing_data.get('aisle', 'Other')
                        )
                        self.db.add(ingredient)
                        self.db.flush()
                    
                    # Create recipe-ingredient relationship
                    recipe_ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient.id,
                        quantity=str(ing_data.get('amount', '')),
                        unit=ing_data.get('unit', '')
                    )
                    self.db.add(recipe_ingredient)
            
            self.db.commit()
            
            logger.info(f"External recipe imported: {recipe.id}")
            
            return {
                "success": True,
                "recipe_id": recipe.id,
                "message": "Recipe imported successfully"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error importing external recipe: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to import recipe"
            }
    
    def sync_recipe_updates(self, external_id: str, source: str = 'spoonacular') -> Dict[str, Any]:
        """Sync updates for externally sourced recipe"""
        
        # Find existing recipe
        from models.recipe import Recipe
        
        recipe = self.db.query(Recipe).filter(
            Recipe.external_api_id == external_id,
            Recipe.external_source == source
        ).first()
        
        if not recipe:
            return {
                "success": False,
                "message": "Recipe not found"
            }
        
        try:
            # Fetch updated data from external API
            # This is a placeholder - implement actual API call
            updated_data = self._fetch_external_recipe_data(external_id, source)
            
            if updated_data:
                # Update recipe with new data
                recipe.title = updated_data.get('title', recipe.title)
                recipe.description = updated_data.get('summary', recipe.description)
                recipe.main_image = updated_data.get('image', recipe.main_image)
                
                self.db.commit()
                
                return {
                    "success": True,
                    "message": "Recipe updated successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "No updates available"
                }
                
        except Exception as e:
            logger.error(f"Error syncing recipe {external_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _fetch_external_recipe_data(self, external_id: str, source: str) -> Optional[Dict[str, Any]]:
        """Fetch recipe data from external API"""
        
        # Placeholder for actual API implementation
        # You would implement the specific API calls here
        
        if source == 'spoonacular':
            # return self._fetch_spoonacular_recipe(external_id)
            pass
        elif source == 'edamam':
            # return self._fetch_edamam_recipe(external_id)
            pass
        
        return None
    
    def get_recipe_suggestions_by_ingredients(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        """Get recipe suggestions from external APIs based on ingredients"""
        
        # Placeholder implementation
        suggestions = []
        
        for i, ingredient in enumerate(ingredients[:3]):  # Limit to first 3 ingredients
            suggestions.append({
                "id": f"ext_{i+1}",
                "title": f"Recipe with {ingredient}",
                "image": f"https://example.com/{ingredient}.jpg",
                "readyInMinutes": 30 + (i * 10),
                "servings": 4,
                "summary": f"A delicious recipe featuring {ingredient}",
                "sourceUrl": f"https://example.com/recipe-{ingredient}",
                "ingredients": ingredients
            })
        
        return suggestions  