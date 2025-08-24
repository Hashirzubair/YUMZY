# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all your API routes
from api import auth, recipes, search, users, favorites, shopping, social
from core.middleware import TimingMiddleware, LoggingMiddleware

app = FastAPI(
    title="YUMZY Recipe Finder API",
    description="🍳 Recipe discovery platform for mobile apps",
    version="1.0.0"
)

# Add middleware
app.add_middleware(TimingMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your mobile app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(recipes.router) 
app.include_router(search.router)
app.include_router(users.router)
app.include_router(favorites.router)
app.include_router(shopping.router)
app.include_router(social.router)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "YUMZY API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
