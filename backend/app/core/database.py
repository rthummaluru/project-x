# backend/app/core/database.py
"""
Database connection and session management.

This file sets up our PostgreSQL connection using SQLAlchemy's async engine.
We use async for better performance with I/O operations (database queries).

Key concepts:
- Engine: Manages database connections
- SessionLocal: Creates database sessions for transactions
- Base: Parent class for all our database models
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
from typing import AsyncGenerator
import logging

from .config import settings

# Set up logging to help with debugging
logger = logging.getLogger(__name__)

# Why async? With 1000 DAU, you'll have multiple concurrent requests.
# Async allows the server to handle other requests while waiting for database I/O.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log all SQL queries in debug mode
    pool_pre_ping=True,   # Verify connections before use (prevents stale connections)
)

# Session factory - creates new database sessions
# Each API request gets its own session for transaction isolation
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects accessible after commit
)

# Base class for all database models
# Provides common functionality like created_at, updated_at timestamps
metadata = MetaData(
    # Naming convention for constraints (helps with migrations)
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

Base = declarative_base(metadata=metadata)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that provides database sessions to API endpoints.
    
    This is a FastAPI dependency that:
    1. Creates a new session for each request
    2. Ensures the session is properly closed after use
    3. Handles transaction rollback on errors
    
    Usage in API endpoints:
    async def create_lead(db: AsyncSession = Depends(get_db)):
        # Use db session here
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Commit transaction if no errors
        except Exception as e:
            await session.rollback()  # Rollback on errors
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            await session.close()  # Always close the session

async def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This function will:
    1. Create all tables defined in your models
    2. Set up indexes for performance
    3. Handle any database initialization logic
    
    Call this once when starting your application.
    """
    try:
        async with engine.begin() as conn:
            # Import all models here so they're registered with Base
            from app.models import company, user, lead, campaign, campaign_email
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def close_db() -> None:
    """
    Clean shutdown of database connections.
    Call this when shutting down your application.
    """
    await engine.dispose()
    logger.info("Database connections closed")