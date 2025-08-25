# database.py

import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Use SQLite database stored locally in yumzy.db file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./yumzy.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Association table for many-to-many relationship between recipes and ingredients
recipe_ingredients = Table(
    'recipe_ingredients',
    Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipes.id'), primary_key=True),
    Column('ingredient_id', Integer, ForeignKey('ingredients.id'), primary_key=True),
    Column('quantity', String(50)),
    Column('unit', String(20))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    bio = Column(Text)
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    is_gluten_free = Column(Boolean, default=False)
    preferred_cuisines = Column(String(500))  # Store as JSON string if needed
    cooking_skill_level = Column(String(20), default="beginner")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    recipes = relationship("Recipe", back_populates="author")
    ratings = relationship("Rating", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")
    shopping_lists = relationship("ShoppingList", back_populates="user")

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    instructions = Column(Text, nullable=False)
    prep_time = Column(Integer)
    cook_time = Column(Integer)
    total_time = Column(Integer)
    servings = Column(Integer)
    difficulty_level = Column(String(20))
    cuisine_type = Column(String(50))
    meal_type = Column(String(50))
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    is_gluten_free = Column(Boolean, default=False)
    main_image = Column(String(255))
    is_published = Column(Boolean, default=True)
    average_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    external_api_id = Column(String(100))
    external_source = Column(String(50))
    source_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User", back_populates="recipes")
    ingredients = relationship("Ingredient", secondary=recipe_ingredients, back_populates="recipes")
    ratings = relationship("Rating", back_populates="recipe")
    favorites = relationship("Favorite", back_populates="recipe")

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    recipes = relationship("Recipe", secondary=recipe_ingredients, back_populates="ingredients")

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, nullable=False)  # 1 to 5 stars
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))

    user = relationship("User", back_populates="ratings")
    recipe = relationship("Recipe", back_populates="ratings")

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))

    user = relationship("User", back_populates="favorites")
    recipe = relationship("Recipe", back_populates="favorites")

class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="shopping_lists")
    items = relationship("ShoppingListItem", back_populates="shopping_list")

class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_name = Column(String(100), nullable=False)
    quantity = Column(String(50))
    unit = Column(String(20))
    is_purchased = Column(Boolean, default=False)
    notes = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    shopping_list_id = Column(Integer, ForeignKey("shopping_lists.id"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=True)

    shopping_list = relationship("ShoppingList", back_populates="items")
    ingredient = relationship("Ingredient")

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    print("✅ Database and tables created successfully.")
