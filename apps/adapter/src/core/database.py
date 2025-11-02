"""Database configuration and session management."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from .config import settings


def get_database_url() -> str:
    """Get the database URL from settings.
    
    Returns:
        Database URL for async connections
    """
    db_url = settings.DATABASE_URL
    
    # Ensure we're using the async driver
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not db_url.startswith("postgresql+asyncpg://"):
        raise ValueError(
            f"Invalid database URL. Expected postgresql+asyncpg:// but got {db_url}"
        )
    
    return db_url


def create_engine(
    database_url: str | None = None,
    pool_size: int | None = None,
    max_overflow: int | None = None,
    echo: bool = False,
    **kwargs: Any,
) -> AsyncEngine:
    """Create an async SQLAlchemy engine.
    
    Args:
        database_url: Database connection URL (defaults to settings)
        pool_size: Connection pool size (defaults to settings)
        max_overflow: Maximum overflow connections (defaults to settings)
        echo: Whether to log SQL statements
        **kwargs: Additional engine options
        
    Returns:
        Configured async engine
    """
    url = database_url or get_database_url()
    pool_size = pool_size or settings.DATABASE_POOL_SIZE
    max_overflow = max_overflow or settings.DATABASE_MAX_OVERFLOW
    
    # Configure pooling
    if "sqlite" in url:
        # SQLite doesn't support connection pooling
        poolclass = NullPool
        pool_kwargs = {}
    else:
        # PostgreSQL with connection pooling
        poolclass = QueuePool
        pool_kwargs = {
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_pre_ping": True,  # Verify connections before using
            "pool_recycle": 3600,  # Recycle connections after 1 hour
        }
    
    engine = create_async_engine(
        url,
        echo=echo,
        poolclass=poolclass,
        future=True,
        **pool_kwargs,
        **kwargs,
    )
    
    return engine


# Global engine instance
engine: AsyncEngine = create_engine(
    echo=settings.debug,
)

# Session factory
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session.
    
    This is a dependency that can be used with FastAPI's Depends.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize the database.
    
    This creates all tables defined in the models.
    Note: In production, use Alembic migrations instead.
    """
    from ..models.base import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close the database connection pool.
    
    This should be called when shutting down the application.
    """
    await engine.dispose()


class DatabaseSession:
    """Context manager for database sessions.
    
    Example:
        async with DatabaseSession() as db:
            result = await db.execute(select(Tenant))
            tenants = result.scalars().all()
    """
    
    def __init__(self) -> None:
        """Initialize the context manager."""
        self.session: AsyncSession | None = None
    
    async def __aenter__(self) -> AsyncSession:
        """Enter the context manager and create a session.
        
        Returns:
            AsyncSession: Database session
        """
        self.session = AsyncSessionFactory()
        return self.session
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the context manager and close the session.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if self.session:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close()