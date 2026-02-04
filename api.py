"""FastAPI backend for Telegram Mini App."""
import logging
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import select
from database import async_session_maker, Flower

logger = logging.getLogger(__name__)

app = FastAPI(title="Flower Bot API", version="1.0.0")

# CORS configuration for Telegram Mini App
# Get allowed origins from environment, default to Telegram domains
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "https://web.telegram.org,https://telegram.org"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for webapp
app.mount("/webapp", StaticFiles(directory="webapp", html=True), name="webapp")


# Response models
class FlowerResponse(BaseModel):
    """Flower model for API responses."""
    id: int
    name: str
    description: Optional[str] = None
    price: float
    photo_url: Optional[str] = None
    category: Optional[str] = None
    available: bool = True

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    """Category response model."""
    category: str
    count: int


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Flower Bot API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/flowers", response_model=List[FlowerResponse])
async def get_flowers(category: Optional[str] = None):
    """
    Get all available flowers, optionally filtered by category.
    
    Args:
        category: Optional category filter (roses, tulips, peonies, mixed, chrysanthemums)
    
    Returns:
        List of available flowers
    """
    try:
        async with async_session_maker() as session:
            query = select(Flower).where(Flower.available == True)
            
            if category and category != "all":
                query = query.where(Flower.category == category)
            
            result = await session.execute(query)
            flowers = result.scalars().all()
            
            return [FlowerResponse.model_validate(flower) for flower in flowers]
    except Exception as e:
        logger.error(f"Error fetching flowers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch flowers")


@app.get("/api/flowers/{flower_id}", response_model=FlowerResponse)
async def get_flower(flower_id: int):
    """
    Get a specific flower by ID.
    
    Args:
        flower_id: The flower ID
    
    Returns:
        Flower details
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Flower).where(Flower.id == flower_id)
            )
            flower = result.scalar_one_or_none()
            
            if not flower:
                raise HTTPException(status_code=404, detail="Flower not found")
            
            return FlowerResponse.model_validate(flower)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching flower {flower_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch flower")


@app.get("/api/categories", response_model=List[CategoryResponse])
async def get_categories():
    """
    Get all available categories with flower counts.
    
    Returns:
        List of categories with counts
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Flower).where(Flower.available == True)
            )
            flowers = result.scalars().all()
            
            # Count flowers by category
            category_counts = {}
            for flower in flowers:
                category = flower.category or "other"
                category_counts[category] = category_counts.get(category, 0) + 1
            
            return [
                CategoryResponse(category=cat, count=count)
                for cat, count in category_counts.items()
            ]
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch categories")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
