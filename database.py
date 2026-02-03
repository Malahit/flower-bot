"""Database models and initialization for flower-bot."""
import os
from datetime import datetime
from typing import Optional, List, AsyncGenerator
from sqlalchemy import String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./flower_bot.db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User model for storing user preferences and reminders."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Preferences
    preferred_colors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    preferred_budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_dates: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string of dates
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")


class Flower(Base):
    """Flower model for catalog items."""
    __tablename__ = "flowers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    """Order model for storing customer orders."""
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Order details
    bouquet_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string with bouquet details
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Delivery information
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    geo_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    geo_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, paid, processing, delivered, cancelled
    payment_status: Mapped[str] = mapped_column(String(50), default="unpaid")  # unpaid, paid, refunded
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ton_stars, etc.
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        yield session


async def add_sample_flowers():
    """Add sample flowers to the database."""
    async with async_session_maker() as session:
        # Check if flowers already exist
        from sqlalchemy import select
        result = await session.execute(select(Flower))
        if result.scalars().first():
            return  # Flowers already exist
        
        sample_flowers = [
            Flower(
                name="Розы классические",
                description="Букет из 15 красных роз",
                price=2500.0,
                photo_url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23",
                category="roses",
                available=True
            ),
            Flower(
                name="Тюльпаны микс",
                description="Букет из 25 разноцветных тюльпанов",
                price=1800.0,
                photo_url="https://images.unsplash.com/photo-1490750967868-88aa4486c946",
                category="tulips",
                available=True
            ),
            Flower(
                name="Пионы нежные",
                description="Букет из 7 розовых пионов",
                price=3200.0,
                photo_url="https://images.unsplash.com/photo-1465146633011-14f8e0781093",
                category="peonies",
                available=True
            ),
            Flower(
                name="Букет 'День рождения'",
                description="Яркий микс из роз, хризантем и альстромерий",
                price=2000.0,
                photo_url="https://images.unsplash.com/photo-1563241527-3004b7be0ffd",
                category="mixed",
                available=True
            ),
            Flower(
                name="Монобукет хризантем",
                description="Букет из белых хризантем",
                price=1500.0,
                photo_url="https://images.unsplash.com/photo-1508610048659-a06b669e3321",
                category="chrysanthemums",
                available=True
            ),
        ]
        
        session.add_all(sample_flowers)
        await session.commit()


async def get_user(user_id: int) -> Optional[User]:
    """Get user from database by user_id."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalars().first()


async def get_popular_flower() -> Optional[Flower]:
    """Get a popular flower for display (first available flower)."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Flower).where(Flower.available == True).limit(1)
        )
        return result.scalars().first()


async def get_user_last_order(user_id: int) -> Optional[Order]:
    """Get user's last order."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()


def format_order_summary(order: Order) -> str:
    """Format order summary for display."""
    if not order:
        return "Нет заказов"
    
    try:
        import json
        bouquet_data = json.loads(order.bouquet_json)
        
        # Extract basic info from first item if available
        if bouquet_data and len(bouquet_data) > 0:
            first_item = bouquet_data[0]
            item_desc = first_item.get('name', first_item.get('color', 'Букет'))
            quantity = first_item.get('quantity', '')
        else:
            item_desc = "Букет"
            quantity = ""
        
        return f"{item_desc} {quantity}".strip()
    except:
        return "Букет"
