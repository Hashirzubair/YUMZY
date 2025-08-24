import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, List
import re

def generate_random_string(length: int = 32) -> str:
    """Generate a random string of specified length"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_string(text: str) -> str:
    """Create SHA256 hash of a string"""
    return hashlib.sha256(text.encode()).hexdigest()

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> List[str]:
    """Validate password strength and return list of errors"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    return errors

def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to URL-friendly slug"""
    # Remove special characters and convert to lowercase
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    # Replace spaces and multiple dashes with single dash
    slug = re.sub(r'[-\s]+', '-', slug)
    # Remove leading/trailing dashes
    slug = slug.strip('-')
    # Truncate to max length
    return slug[:max_length]

def format_cooking_time(minutes: Optional[int]) -> str:
    """Format cooking time in human-readable format"""
    if not minutes:
        return "N/A"
    
    if minutes < 60:
        return f"{minutes} min"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours} hr"
    
    return f"{hours} hr {remaining_minutes} min"

def calculate_recipe_score(
    view_count: int = 0,
    favorite_count: int = 0,
    rating_count: int = 0,
    average_rating: float = 0.0
) -> float:
    """Calculate a composite score for recipe ranking"""
    # Weighted scoring system
    view_score = min(view_count * 0.1, 50)  # Cap at 50 points
    favorite_score = favorite_count * 2
    rating_score = (average_rating * rating_count) if rating_count > 0 else 0
    
    return view_score + favorite_score + rating_score

def parse_ingredient_quantity(quantity_str: str) -> dict:
    """Parse ingredient quantity string into amount and unit"""
    if not quantity_str:
        return {"amount": None, "unit": None}
    
    # Common patterns for quantities
    patterns = [
        r'(\d+\.?\d*)\s*(\w+)',  # "2 cups", "1.5 tbsp"
        r'(\d+/\d+)\s*(\w+)',    # "1/2 cup"
        r'(\d+)\s*(\w+)',        # "3 cloves"
        r'(\d+\.?\d*)',          # Just number
    ]
    
    for pattern in patterns:
        match = re.match(pattern, quantity_str.strip())
        if match:
            if len(match.groups()) == 2:
                return {"amount": match.group(1), "unit": match.group(2)}
            else:
                return {"amount": match.group(1), "unit": None}
    
    # If no pattern matches, return original string as unit
    return {"amount": None, "unit": quantity_str}

def normalize_cuisine_name(cuisine: str) -> str:
    """Normalize cuisine name for consistency"""
    if not cuisine:
        return "International"
    
    cuisine_mapping = {
        "italian": "Italian",
        "chinese": "Chinese", 
        "mexican": "Mexican",
        "indian": "Indian",
        "french": "French",
        "japanese": "Japanese",
        "american": "American",
        "thai": "Thai",
        "greek": "Greek",
        "spanish": "Spanish",
        "mediterranean": "Mediterranean",
        "middle eastern": "Middle Eastern",
        "korean": "Korean",
        "vietnamese": "Vietnamese"
    }
    
    return cuisine_mapping.get(cuisine.lower(), cuisine.title())

def calculate_pagination(page: int, limit: int, total_count: int) -> dict:
    """Calculate pagination metadata"""
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
    
    return {
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "next_page": page + 1 if page < total_pages else None,
        "prev_page": page - 1 if page > 1 else None
    }

def clean_html_tags(text: str) -> str:
    """Remove HTML tags from text"""
    if not text:
        return ""
    
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Remove extra whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    return clean

def generate_recipe_url_slug(title: str, recipe_id: int) -> str:
    """Generate SEO-friendly URL slug for recipe"""
    base_slug = slugify(title)
    return f"{base_slug}-{recipe_id}"

def format_ingredient_list(ingredients: List[dict]) -> List[str]:
    """Format ingredient list for display"""
    formatted = []
    
    for ingredient in ingredients:
        name = ingredient.get('name', '')
        quantity = ingredient.get('quantity', '')
        unit = ingredient.get('unit', '')
        
        if quantity and unit:
            formatted.append(f"{quantity} {unit} {name}")
        elif quantity:
            formatted.append(f"{quantity} {name}")
        else:
            formatted.append(name)
    
    return formatted

def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Estimate reading time for recipe instructions"""
    if not text:
        return 0
    
    word_count = len(text.split())
    reading_time = max(1, round(word_count / words_per_minute))
    
    return reading_time

def format_nutritional_info(nutrition_data: dict) -> dict:
    """Format nutritional information for display"""
    if not nutrition_data:
        return {}
    
    formatted = {}
    
    # Format each nutritional value
    for key, value in nutrition_data.items():
        if isinstance(value, (int, float)):
            if key.endswith('_g'):
                formatted[key] = f"{value:.1f}g"
            elif key.endswith('_mg'):
                formatted[key] = f"{value:.0f}mg"
            elif key == 'calories':
                formatted[key] = f"{value:.0f}"
            else:
                formatted[key] = str(value)
        else:
            formatted[key] = str(value)
    
    return formatted

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if division by zero"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_difficulty_color(difficulty: str) -> str:
    """Get color code for difficulty level"""
    colors = {
        "easy": "#28a745",     # Green
        "medium": "#ffc107",   # Yellow
        "hard": "#dc3545"      # Red
    }
    
    return colors.get(difficulty.lower(), "#6c757d")  # Gray default

def format_recipe_stats(recipe_data: dict) -> dict:
    """Format recipe statistics for display"""
    return {
        "views": f"{recipe_data.get('view_count', 0):,}",
        "favorites": f"{recipe_data.get('favorite_count', 0):,}",
        "ratings": f"{recipe_data.get('rating_count', 0):,}",
        "average_rating": f"{recipe_data.get('average_rating', 0.0):.1f}",
        "difficulty": recipe_data.get('difficulty_level', 'Unknown').title(),
        "prep_time": format_cooking_time(recipe_data.get('prep_time')),
        "cook_time": format_cooking_time(recipe_data.get('cook_time')),
        "total_time": format_cooking_time(recipe_data.get('total_time'))
    }