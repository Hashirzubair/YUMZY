from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class BaseSchema(BaseModel):
    model_config = {
        "from_attributes": True
    }

# Authentication schemas
class UserCreate(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseSchema):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str]
    bio: Optional[str]
    is_vegetarian: bool
    is_vegan: bool
    is_gluten_free: bool
    preferred_cuisines: Optional[str]
    cooking_skill_level: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

class UserUpdate(BaseSchema):
    full_name: Optional[str]
    bio: Optional[str]
    is_vegetarian: Optional[bool]
    is_vegan: Optional[bool]
    is_gluten_free: Optional[bool]
    preferred_cuisines: Optional[str]
    cooking_skill_level: Optional[str]

# Ingredient schema in recipe
class IngredientInRecipe(BaseSchema):
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None

# Recipe schemas
class RecipeCreate(BaseSchema):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    instructions: str = Field(..., min_length=10)
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    difficulty_level: Optional[str] = None
    cuisine_type: Optional[str] = None
    meal_type: Optional[str] = None
    ingredients: List[IngredientInRecipe] = []

class RecipeUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    difficulty_level: Optional[str] = None
    cuisine_type: Optional[str] = None
    meal_type: Optional[str] = None
    is_published: Optional[bool] = None

class RecipeResponse(BaseSchema):
    id: int
    title: str
    description: Optional[str]
    instructions: str
    prep_time: Optional[int]
    cook_time: Optional[int]
    total_time: Optional[int]
    servings: Optional[int]
    difficulty_level: Optional[str]
    cuisine_type: Optional[str]
    meal_type: Optional[str]
    is_vegetarian: bool
    is_vegan: bool
    is_gluten_free: bool
    main_image: Optional[str]
    average_rating: float
    rating_count: int
    view_count: int
    favorite_count: int
    created_at: datetime
    author_id: int
    author_username: Optional[str]
    ingredients: List[IngredientInRecipe]
    is_favorited: bool = False
    user_rating: Optional[int] = None

class RecipeDetailed(RecipeResponse):
    similar_recipes: List[RecipeResponse] = []

class RecipeListResponse(BaseSchema):
    recipes: List[RecipeResponse]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

# Search Response Schema
class SearchResponse(RecipeListResponse):
    filters: dict

# Ingredient Search Response
class IngredientResponse(BaseSchema):
    id: int
    name: str
    category: Optional[str] = None

# Rating schemas
class RatingCreate(BaseSchema):
    recipe_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class RatingResponse(BaseSchema):
    id: int
    rating: int
    comment: Optional[str]
    user_id: int
    recipe_id: int
    username: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

# Favorite schemas
class FavoriteCreate(BaseSchema):
    recipe_id: int
    notes: Optional[str] = None

class FavoriteResponse(BaseSchema):
    id: int
    recipe_id: int
    recipe_title: str
    recipe_image: Optional[str] = None
    notes: Optional[str]
    created_at: datetime

# Shopping List schemas
class ShoppingListCreate(BaseSchema):
    name: str
    description: Optional[str] = None

class ShoppingListItemCreate(BaseSchema):
    ingredient_name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None

class ShoppingListItemResponse(ShoppingListItemCreate):
    id: int
    is_purchased: bool = False
    created_at: datetime

class ShoppingListResponse(BaseSchema):
    id: int
    name: str
    description: Optional[str] = None
    is_completed: bool = False
    created_at: datetime
    items: List[ShoppingListItemResponse] = []
    total_items: int = 0
    purchased_items: int = 0

class ShoppingListUpdate(BaseSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None

# User analytics schemas
class UserStats(BaseSchema):
    user_id: int
    username: str
    recipe_count: int = 0
    favorite_count: int = 0
    rating_count: int = 0
    average_rating_received: float = 0.0
    member_since: datetime

class UserAnalytics(BaseSchema):
    user_id: int
    total_recipes: int = 0
    total_favorites_given: int = 0
    total_ratings_given: int = 0
    total_views_received: int = 0
    total_favorites_received: int = 0
    most_popular_recipe_title: Optional[str] = None
    most_popular_recipe_views: int = 0
    favorite_cuisine: Optional[str] = None
    account_created: datetime
    last_active: Optional[datetime]
