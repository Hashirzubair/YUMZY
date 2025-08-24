from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums for better type safety
class DietaryType(str, Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    NUT_FREE = "nut_free"
    KETO = "keto"
    PALEO = "paleo"

class CuisineType(str, Enum):
    ITALIAN = "italian"
    CHINESE = "chinese"
    MEXICAN = "mexican"
    INDIAN = "indian"
    FRENCH = "french"
    JAPANESE = "japanese"
    AMERICAN = "american"
    THAI = "thai"
    GREEK = "greek"
    SPANISH = "spanish"
    MIDDLE_EASTERN = "middle_eastern"

class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
    DESSERT = "dessert"
    APPETIZER = "appetizer"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

# Base schemas
class BaseSchema(BaseModel):
    class Config:
        orm_mode = True
        use_enum_values = True

# User schemas
class UserBase(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserUpdate(BaseSchema):
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    profile_picture: Optional[str] = None
    is_vegetarian: Optional[bool] = None
    is_vegan: Optional[bool] = None
    is_gluten_free: Optional[bool] = None
    is_dairy_free: Optional[bool] = None
    is_nut_free: Optional[bool] = None
    allergies: Optional[List[str]] = None
    preferred_cuisines: Optional[List[CuisineType]] = None
    cooking_skill_level: Optional[SkillLevel] = None

class UserResponse(UserBase):
    id: int
    uuid: str
    profile_picture: Optional[str] = None
    is_vegetarian: bool = False
    is_vegan: bool = False
    is_gluten_free: bool = False
    is_dairy_free: bool = False
    is_nut_free: bool = False
    allergies: Optional[List[str]] = None
    preferred_cuisines: Optional[List[str]] = None
    cooking_skill_level: str = "beginner"
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

class UserProfile(UserResponse):
    recipe_count: Optional[int] = 0
    favorite_count: Optional[int] = 0
    rating_count: Optional[int] = 0
    average_rating_given: Optional[float] = 0.0

# Authentication schemas
class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseSchema):
    user_id: Optional[int] = None
    username: Optional[str] = None

class UserLogin(BaseSchema):
    username: str
    password: str

# Recipe schemas
class RecipeBase(BaseSchema):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    instructions: str = Field(..., min_length=10)
    prep_time: Optional[int] = Field(None, ge=0, le=1440)  # max 24 hours
    cook_time: Optional[int] = Field(None, ge=0, le=1440)
    servings: Optional[int] = Field(None, ge=1, le=50)
    difficulty_level: Optional[DifficultyLevel] = None
    cuisine_type: Optional[CuisineType] = None
    meal_type: Optional[MealType] = None

class RecipeCreate(RecipeBase):
    ingredient_ids: List[int] = Field(..., min_items=1)
    ingredient_quantities: List[str] = Field(..., min_items=1)
    ingredient_units: List[str] = Field(..., min_items=1)
    category_ids: Optional[List[int]] = []
    
    @validator('ingredient_quantities', 'ingredient_units')
    def validate_ingredient_lists(cls, v, values):
        if 'ingredient_ids' in values and len(v) != len(values['ingredient_ids']):
            raise ValueError('Ingredient quantities and units must match ingredient count')
        return v

class RecipeUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    instructions: Optional[str] = Field(None, min_length=10)
    prep_time: Optional[int] = Field(None, ge=0, le=1440)
    cook_time: Optional[int] = Field(None, ge=0, le=1440)
    servings: Optional[int] = Field(None, ge=1, le=50)
    difficulty_level: Optional[DifficultyLevel] = None
    cuisine_type: Optional[CuisineType] = None
    meal_type: Optional[MealType] = None
    is_published: Optional[bool] = None

class IngredientInRecipe(BaseSchema):
    id: int
    name: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None

class RecipeResponse(RecipeBase):
    id: int
    uuid: str
    total_time: Optional[int] = None
    calories_per_serving: Optional[int] = None
    is_vegetarian: bool = False
    is_vegan: bool = False
    is_gluten_free: bool = False
    is_dairy_free: bool = False
    is_nut_free: bool = False
    main_image: Optional[str] = None
    additional_images: Optional[List[str]] = []
    video_url: Optional[str] = None
    average_rating: float = 0.0
    rating_count: int = 0
    view_count: int = 0
    favorite_count: int = 0
    is_published: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    author_id: int
    author_username: Optional[str] = None
    ingredients: List[IngredientInRecipe] = []
    categories: List[str] = []

class RecipeDetailed(RecipeResponse):
    nutrition_facts: Optional[Dict[str, Any]] = None
    similar_recipes: List["RecipeResponse"] = []
    user_rating: Optional[int] = None
    is_favorited: bool = False
    source_url: Optional[str] = None

# Ingredient schemas
class IngredientBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)

class IngredientCreate(IngredientBase):
    calories_per_100g: Optional[int] = Field(None, ge=0)
    protein_per_100g: Optional[float] = Field(None, ge=0)
    carbs_per_100g: Optional[float] = Field(None, ge=0)
    fat_per_100g: Optional[float] = Field(None, ge=0)
    substitutes: Optional[List[str]] = []
    storage_tips: Optional[str] = None
    shelf_life_days: Optional[int] = Field(None, ge=1)

class IngredientResponse(IngredientBase):
    id: int
    calories_per_100g: Optional[int] = None
    protein_per_100g: Optional[float] = None
    carbs_per_100g: Optional[float] = None
    fat_per_100g: Optional[float] = None
    substitutes: Optional[List[str]] = []
    is_vegetarian: bool = True
    is_vegan: bool = True
    is_gluten_free: bool = True
    is_dairy_free: bool = True
    storage_tips: Optional[str] = None
    shelf_life_days: Optional[int] = None
    created_at: datetime

# Rating schemas
class RatingBase(BaseSchema):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)

class RatingCreate(RatingBase):
    recipe_id: int

class RatingUpdate(BaseSchema):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)

class RatingResponse(RatingBase):
    id: int
    user_id: int
    recipe_id: int
    username: Optional[str] = None
    helpful_count: int = 0
    total_votes: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

# Favorite schemas
class FavoriteCreate(BaseSchema):
    recipe_id: int
    notes: Optional[str] = Field(None, max_length=500)

class FavoriteResponse(BaseSchema):
    id: int
    recipe_id: int
    recipe_title: str
    recipe_image: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

# Shopping list schemas
class ShoppingListBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ShoppingListCreate(ShoppingListBase):
    pass

class ShoppingListItemCreate(BaseSchema):
    ingredient_name: str = Field(..., min_length=1, max_length=100)
    quantity: Optional[str] = Field(None, max_length=50)
    unit: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=255)
    ingredient_id: Optional[int] = None

class ShoppingListItemResponse(ShoppingListItemCreate):
    id: int
    is_purchased: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

class ShoppingListResponse(ShoppingListBase):
    id: int
    is_completed: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[ShoppingListItemResponse] = []
    total_items: int = 0
    purchased_items: int = 0

# Search and filter schemas
class RecipeSearchFilters(BaseSchema):
    query: Optional[str] = Field(None, max_length=200)
    ingredients: Optional[List[str]] = []
    cuisine_types: Optional[List[CuisineType]] = []
    meal_types: Optional[List[MealType]] = []
    dietary_restrictions: Optional[List[DietaryType]] = []
    difficulty_levels: Optional[List[DifficultyLevel]] = []
    max_prep_time: Optional[int] = Field(None, ge=0)
    max_cook_time: Optional[int] = Field(None, ge=0)
    max_total_time: Optional[int] = Field(None, ge=0)
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    max_calories: Optional[int] = Field(None, ge=0)
    servings: Optional[int] = Field(None, ge=1)

class PaginationParams(BaseSchema):
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)

class SearchResponse(BaseSchema):
    recipes: List[RecipeResponse]
    total_count: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
    filters_applied: RecipeSearchFilters

# Category schemas
class CategoryBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    icon: Optional[str] = None
    color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$')

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    is_active: bool = True
    sort_order: int = 0
    recipe_count: Optional[int] = 0
    created_at: datetime

# Collection schemas
class CollectionBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: bool = False

class CollectionCreate(CollectionBase):
    recipe_ids: Optional[List[int]] = []

class CollectionUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None
    cover_image: Optional[str] = None

class CollectionResponse(CollectionBase):
    id: int
    user_id: int
    cover_image: Optional[str] = None
    recipe_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    recipes: List[RecipeResponse] = []

# Social sharing schemas
class SocialShareCreate(BaseSchema):
    platform: str = Field(..., regex=r'^(facebook|twitter|instagram|whatsapp|pinterest)$')
    recipe_id: int

class SocialShareResponse(BaseSchema):
    id: int
    platform: str
    recipe_id: int
    share_url: str
    share_count: int
    created_at: datetime

# Analytics schemas
class UserAnalytics(BaseSchema):
    total_recipes: int = 0
    total_favorites: int = 0
    total_ratings: int = 0
    average_rating_received: float = 0.0
    total_views: int = 0
    recipes_this_month: int = 0
    favorite_cuisine: Optional[str] = None
    cooking_streak_days: int = 0

class RecipeAnalytics(BaseSchema):
    recipe_id: int
    total_views: int = 0
    total_favorites: int = 0
    total_ratings: int = 0
    average_rating: float = 0.0
    shares_by_platform: Dict[str, int] = {}
    views_last_30_days: int = 0
    engagement_rate: float = 0.0

# Recommendation schemas
class RecommendationRequest(BaseSchema):
    based_on: str = Field(..., regex=r'^(favorites|ratings|ingredients|cuisine|dietary)$')
    limit: int = Field(10, ge=1, le=50)
    exclude_recipe_ids: Optional[List[int]] = []

class RecommendationResponse(BaseSchema):
    recipes: List[RecipeResponse]
    recommendation_reason: str
    confidence_score: float = Field(..., ge=0, le=1)

# Error schemas
class ErrorResponse(BaseSchema):
    error: bool = True
    message: str
    details: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None

# Success schemas
class SuccessResponse(BaseSchema):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

# File upload schemas
class FileUpload(BaseSchema):
    file_url: str
    file_type: str
    file_size: int
    uploaded_at: datetime

class ImageUploadResponse(BaseSchema):
    success: bool
    file_url: str
    file_name: str
    file_size: int
    image_width: Optional[int] = None
    image_height: Optional[int] = None

# Fix forward references
RecipeDetailed.update_forward_refs()