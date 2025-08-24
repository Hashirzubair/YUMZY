from sqlalchemy import create_engine, MetaData, Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

# Database configuration
DATABASE_URL = "postgresql://yumzy_user:yumzy_password@localhost:5432/yumzy_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association tables for many-to-many relationships
recipe_ingredients = Table(
    'recipe_ingredients',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id'), primary_key=True),
    Column('ingredient_id', Integer, ForeignKey('ingredients.id'), primary_key=True),
    Column('quantity', String(50)),
    Column('unit', String(20))
)

recipe_categories = Table(
    'recipe_categories',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

# User model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    profile_picture = Column(String(255))
    bio = Column(Text)
    
    # Dietary preferences
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    is_gluten_free = Column(Boolean, default=False)
    is_dairy_free = Column(Boolean, default=False)
    is_nut_free = Column(Boolean, default=False)
    allergies = Column(ARRAY(String))
    
    # User preferences
    preferred_cuisines = Column(ARRAY(String))
    cooking_skill_level = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    recipes = relationship("Recipe", back_populates="author")
    ratings = relationship("Rating", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")
    shopping_lists = relationship("ShoppingList", back_populates="user")

# Recipe model
class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    instructions = Column(Text, nullable=False)
    
    # Recipe metadata
    prep_time = Column(Integer)  # minutes
    cook_time = Column(Integer)  # minutes
    total_time = Column(Integer)  # minutes
    servings = Column(Integer)
    difficulty_level = Column(String(20))  # easy, medium, hard
    
    # Nutritional information (per serving)
    calories_per_serving = Column(Integer)
    protein_grams = Column(Float)
    carbs_grams = Column(Float)
    fat_grams = Column(Float)
    fiber_grams = Column(Float)
    
    # Recipe characteristics
    cuisine_type = Column(String(50))
    meal_type = Column(String(50))  # breakfast, lunch, dinner, snack, dessert
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    is_gluten_free = Column(Boolean, default=False)
    is_dairy_free = Column(Boolean, default=False)
    is_nut_free = Column(Boolean, default=False)
    
    # Media
    main_image = Column(String(255))
    additional_images = Column(ARRAY(String))
    video_url = Column(String(255))
    
    # Recipe status and metrics
    is_published = Column(Boolean, default=True)
    average_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    
    # External API data
    external_api_id = Column(String(100))
    external_source = Column(String(50))
    source_url = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    author_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    author = relationship("User", back_populates="recipes")
    ingredients = relationship("Ingredient", secondary=recipe_ingredients, back_populates="recipes")
    categories = relationship("Category", secondary=recipe_categories, back_populates="recipes")
    ratings = relationship("Rating", back_populates="recipe")
    favorites = relationship("Favorite", back_populates="recipe")
    nutrition_facts = relationship("NutritionFact", back_populates="recipe")

# Ingredient model
class Ingredient(Base):
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50))  # vegetable, meat, dairy, spice, etc.
    description = Column(Text)
    
    # Nutritional information (per 100g)
    calories_per_100g = Column(Integer)
    protein_per_100g = Column(Float)
    carbs_per_100g = Column(Float)
    fat_per_100g = Column(Float)
    
    # Common substitutes
    substitutes = Column(ARRAY(String))
    
    # Dietary flags
    is_vegetarian = Column(Boolean, default=True)
    is_vegan = Column(Boolean, default=True)
    is_gluten_free = Column(Boolean, default=True)
    is_dairy_free = Column(Boolean, default=True)
    
    # Storage information
    storage_tips = Column(Text)
    shelf_life_days = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    recipes = relationship("Recipe", secondary=recipe_ingredients, back_populates="ingredients")

# Category model
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    icon = Column(String(100))
    color = Column(String(7))  # hex color
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    recipes = relationship("Recipe", secondary=recipe_categories, back_populates="categories")

# Rating model
class Rating(Base):
    __tablename__ = "ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text)
    is_verified_purchase = Column(Boolean, default=False)
    
    # Helpful votes
    helpful_count = Column(Integer, default=0)
    total_votes = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    
    # Relationships
    user = relationship("User", back_populates="ratings")
    recipe = relationship("Recipe", back_populates="ratings")

# Favorite recipes model
class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    recipe = relationship("Recipe", back_populates="favorites")

# Shopping list model
class ShoppingList(Base):
    __tablename__ = "shopping_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_completed = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="shopping_lists")
    items = relationship("ShoppingListItem", back_populates="shopping_list")

# Shopping list item model
class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"
    
    id = Column(Integer, primary_key=True, index=True)
    ingredient_name = Column(String(100), nullable=False)
    quantity = Column(String(50))
    unit = Column(String(20))
    is_purchased = Column(Boolean, default=False)
    notes = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    shopping_list_id = Column(Integer, ForeignKey("shopping_lists.id"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=True)
    
    # Relationships
    shopping_list = relationship("ShoppingList", back_populates="items")
    ingredient = relationship("Ingredient")

# Nutrition facts model (detailed nutritional information)
class NutritionFact(Base):
    __tablename__ = "nutrition_facts"
    
    id = Column(Integer, primary_key=True, index=True)
    serving_size = Column(String(50))
    calories = Column(Integer)
    total_fat_g = Column(Float)
    saturated_fat_g = Column(Float)
    trans_fat_g = Column(Float)
    cholesterol_mg = Column(Float)
    sodium_mg = Column(Float)
    total_carbs_g = Column(Float)
    dietary_fiber_g = Column(Float)
    sugars_g = Column(Float)
    protein_g = Column(Float)
    vitamin_a_percent = Column(Float)
    vitamin_c_percent = Column(Float)
    calcium_percent = Column(Float)
    iron_percent = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    
    # Relationships
    recipe = relationship("Recipe", back_populates="nutrition_facts")

# Recipe collection model (user-created recipe collections)
class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    cover_image = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User")
    recipes = relationship("Recipe", secondary="collection_recipes")

# Association table for collections and recipes
collection_recipes = Table(
    'collection_recipes',
    Base.metadata,
    Column('collection_id', Integer, ForeignKey('collections.id'), primary_key=True),
    Column('recipe_id', Integer, ForeignKey('recipes.id'), primary_key=True),
    Column('added_at', DateTime(timezone=True), server_default=func.now())
)

# Social sharing model
class SocialShare(Base):
    __tablename__ = "social_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50))  # facebook, twitter, instagram, whatsapp
    share_url = Column(String(500))
    share_count = Column(Integer, default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    
    # Relationships
    user = relationship("User")
    recipe = relationship("Recipe")

# Recipe view tracking
class RecipeView(Base):
    __tablename__ = "recipe_views"
    
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    
    # Relationships
    user = relationship("User")
    recipe = relationship("Recipe")

# Database initialization
def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()