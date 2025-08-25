from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, Float
)
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    full_name = Column(String(100))
    password_hash = Column(String(128))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Recipe(Base):
    __tablename__ = 'recipes'
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    instructions = Column(Text)
    prep_time = Column(Integer)
    cook_time = Column(Integer)
    servings = Column(Integer)
    cuisine_type = Column(String(50))
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User")
    ingredients = relationship("Ingredient", back_populates="recipe")
    ratings = relationship("Rating", back_populates="recipe")
    favorites = relationship("Favorite", back_populates="recipe")

class Ingredient(Base):
    __tablename__ = 'ingredients'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    quantity = Column(String(50))
    recipe_id = Column(Integer, ForeignKey('recipes.id'))
    recipe = relationship("Recipe", back_populates="ingredients")

class Favorite(Base):
    __tablename__ = 'favorites'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    recipe_id = Column(Integer, ForeignKey('recipes.id'))
    notes = Column(Text)
    user = relationship("User")
    recipe = relationship("Recipe", back_populates="favorites")

class Rating(Base):
    __tablename__ = 'ratings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    recipe_id = Column(Integer, ForeignKey('recipes.id'))
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User")
    recipe = relationship("Recipe", back_populates="ratings")
