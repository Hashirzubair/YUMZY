from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from models.user import User
from models.recipe import Recipe
from models.favorite import Favorite
from models.rating import Rating
from schemas.user import UserResponse, UserUpdate, UserStats, UserAnalytics
from core.exceptions import UserNotFoundError
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service class for user-related business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> UserResponse:
        """Update user profile"""
        
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User profile updated: {user_id}")
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            bio=user.bio,
            is_vegetarian=user.is_vegetarian,
            is_vegan=user.is_vegan,
            is_gluten_free=user.is_gluten_free,
            preferred_cuisines=user.preferred_cuisines or [],
            cooking_skill_level=user.cooking_skill_level,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
    
    def delete_user(self, user_id: int) -> None:
        """Delete user account"""
        
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # Soft delete by marking as inactive
        user.is_active = False
        self.db.commit()
        
        logger.info(f"User account deactivated: {user_id}")
    
    def get_user_stats(self, user_id: int) -> UserStats:
        """Get public user statistics"""
        
        user = self.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise UserNotFoundError()
        
        # Count user's recipes
        recipe_count = self.db.query(func.count(Recipe.id)).filter(
            Recipe.author_id == user_id,
            Recipe.is_published == True
        ).scalar() or 0
        
        # Count user's favorites
        favorite_count = self.db.query(func.count(Favorite.id)).filter(
            Favorite.user_id == user_id
        ).scalar() or 0
        
        # Count ratings given by user
        rating_count = self.db.query(func.count(Rating.id)).filter(
            Rating.user_id == user_id
        ).scalar() or 0
        
        # Average rating of user's recipes
        avg_rating_received = self.db.query(func.avg(Recipe.average_rating)).filter(
            Recipe.author_id == user_id,
            Recipe.is_published == True,
            Recipe.rating_count > 0
        ).scalar() or 0.0
        
        return UserStats(
            user_id=user_id,
            username=user.username,
            recipe_count=recipe_count,
            favorite_count=favorite_count,
            rating_count=rating_count,
            average_rating_received=float(avg_rating_received),
            member_since=user.created_at
        )
    
    def get_user_analytics(self, user_id: int) -> UserAnalytics:
        """Get detailed user analytics (private)"""
        
        user = self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        # Basic stats
        recipe_count = self.db.query(func.count(Recipe.id)).filter(
            Recipe.author_id == user_id,
            Recipe.is_published == True
        ).scalar() or 0
        
        favorite_count = self.db.query(func.count(Favorite.id)).filter(
            Favorite.user_id == user_id
        ).scalar() or 0
        
        rating_count = self.db.query(func.count(Rating.id)).filter(
            Rating.user_id == user_id
        ).scalar() or 0
        
        # Total views on user's recipes
        total_views = self.db.query(func.sum(Recipe.view_count)).filter(
            Recipe.author_id == user_id,
            Recipe.is_published == True
        ).scalar() or 0
        
        # Total favorites on user's recipes
        total_favorites_received = self.db.query(func.sum(Recipe.favorite_count)).filter(
            Recipe.author_id == user_id,
            Recipe.is_published == True
        ).scalar() or 0
        
        # Most popular recipe
        popular_recipe = self.db.query(Recipe).filter(
            Recipe.author_id == user_id,
            Recipe.is_published == True
        ).order_by(desc(Recipe.view_count)).first()
        
        # Favorite cuisine (most used in user's recipes)
        favorite_cuisine = self.db.query(Recipe.cuisine_type).filter(
            Recipe.author_id == user_id,
            Recipe.is_published == True,
            Recipe.cuisine_type.isnot(None)
        ).group_by(Recipe.cuisine_type).order_by(
            desc(func.count(Recipe.cuisine_type))
        ).first()
        
        return UserAnalytics(
            user_id=user_id,
            total_recipes=recipe_count,
            total_favorites_given=favorite_count,
            total_ratings_given=rating_count,
            total_views_received=int(total_views),
            total_favorites_received=int(total_favorites_received),
            most_popular_recipe_title=popular_recipe.title if popular_recipe else None,
            most_popular_recipe_views=popular_recipe.view_count if popular_recipe else 0,
            favorite_cuisine=favorite_cuisine[0] if favorite_cuisine else None,
            account_created=user.created_at,
            last_active=user.last_login
        )
    
    def get_user_recipe_history(self, user_id: int, page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's recipe creation history"""
        
        offset = (page - 1) * limit
        
        recipes = self.db.query(Recipe).filter(
            Recipe.author_id == user_id
        ).order_by(desc(Recipe.created_at)).offset(offset).limit(limit).all()
        
        return [
            {
                "id": recipe.id,
                "title": recipe.title,
                "cuisine_type": recipe.cuisine_type,
                "meal_type": recipe.meal_type,
                "is_published": recipe.is_published,
                "view_count": recipe.view_count or 0,
                "favorite_count": recipe.favorite_count or 0,
                "rating_count": recipe.rating_count or 0,
                "average_rating": recipe.average_rating or 0.0,
                "created_at": recipe.created_at
            }
            for recipe in recipes
        ]
    
    def get_user_favorite_cuisines(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's favorite cuisines based on favorites"""
        
        favorite_cuisines = self.db.query(
            Recipe.cuisine_type,
            func.count(Recipe.cuisine_type).label('count')
        ).join(Favorite).filter(
            Favorite.user_id == user_id,
            Recipe.cuisine_type.isnot(None)
        ).group_by(Recipe.cuisine_type).order_by(
            desc('count')
        ).limit(10).all()
        
        return [
            {
                "cuisine_type": cuisine,
                "favorite_count": count
            }
            for cuisine, count in favorite_cuisines
        ]
    
    def get_user_activity_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary for the last N days"""
        
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Recipes created in period
        recipes_created = self.db.query(func.count(Recipe.id)).filter(
            Recipe.author_id == user_id,
            Recipe.created_at >= start_date
        ).scalar() or 0
        
        # Favorites added in period
        favorites_added = self.db.query(func.count(Favorite.id)).filter(
            Favorite.user_id == user_id,
            Favorite.created_at >= start_date
        ).scalar() or 0
        
        # Ratings given in period
        ratings_given = self.db.query(func.count(Rating.id)).filter(
            Rating.user_id == user_id,
            Rating.created_at >= start_date
        ).scalar() or 0
        
        return {
            "period_days": days,
            "recipes_created": recipes_created,
            "favorites_added": favorites_added,
            "ratings_given": ratings_given,
            "total_activity": recipes_created + favorites_added + ratings_given
        }