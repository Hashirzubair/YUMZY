from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from database import create_tables
from api.auth import router as auth_router
# Import other routers similarly: recipes_router, search_router, etc.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting YUMZY API...")
    create_tables()
    logger.info("Tables created")
    yield
    logger.info("Shutting down YUMZY API...")

app = FastAPI(
    title="YUMZY Recipe Finder API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": True, "message": exc.detail})

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": True, "message": "Internal server error"})

app.include_router(auth_router)
# Include other routers: recipes_router, users_router, favorites_router, etc.
