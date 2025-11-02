"""Database configuration and session management."""

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


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
        # PostgreSQL with connection pooling for async
        poolclass = NullPool  # Async engines don't use QueuePool
        pool_kwargs = {}
    
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


async def set_tenant_context(session: AsyncSession, tenant_id: UUID) -> None:
    """Set the tenant context for Row-Level Security (RLS).
    
    This sets the app.current_tenant_id PostgreSQL session variable that is used
    by RLS policies to filter data by tenant. This MUST be called at the start
    of every request/transaction to ensure proper tenant isolation.
    
    Args:
        session: The database session
        tenant_id: UUID of the current tenant
        
    Raises:
        Exception: If setting the context fails
        
    Example:
        async with AsyncSessionFactory() as session:
            await set_tenant_context(session, tenant_id)
            # Now all queries are automatically filtered by tenant_id
            result = await session.execute(select(ActionLog))
    """
    try:
        # Set the session variable that RLS policies use
        await session.execute(
            text("SET LOCAL app.current_tenant_id = :tenant_id"),
            {"tenant_id": str(tenant_id)}
        )
        logger.debug(f"Set tenant context to {tenant_id}")
    except Exception as e:
        logger.error(f"Failed to set tenant context for {tenant_id}: {e}")
        raise


async def clear_tenant_context(session: AsyncSession) -> None:
    """Clear the tenant context from the session.
    
    This removes the app.current_tenant_id session variable. Primarily used
    for cleanup or when switching contexts within the same session.
    
    Args:
        session: The database session
        
    Note:
        Not strictly necessary if using SET LOCAL, as it's automatically
        cleared at transaction end. Included for explicit cleanup.
    """
    try:
        await session.execute(
            text("RESET app.current_tenant_id")
        )
        logger.debug("Cleared tenant context")
    except Exception as e:
        logger.warning(f"Failed to clear tenant context: {e}")


class DatabaseSession:
    """Context manager for database sessions with tenant context support.
    
    This context manager automatically handles tenant context for RLS.
    If a tenant_id is provided, it sets the tenant context before any queries.
    
    Examples:
        # Without tenant context (for admin operations):
        async with DatabaseSession() as db:
            result = await db.execute(select(Tenant))
            tenants = result.scalars().all()
        
        # With tenant context (for tenant-scoped operations):
        async with DatabaseSession(tenant_id=tenant_uuid) as db:
            # All queries automatically filtered by tenant_id via RLS
            result = await db.execute(select(ActionLog))
            logs = result.scalars().all()
    """
    
    def __init__(self, tenant_id: UUID | None = None) -> None:
        """Initialize the context manager.
        
        Args:
            tenant_id: Optional tenant UUID to set context for RLS
        """
        self.session: AsyncSession | None = None
        self.tenant_id = tenant_id
    
    async def __aenter__(self) -> AsyncSession:
        """Enter the context manager and create a session.
        
        If tenant_id was provided, sets the tenant context for RLS.
        
        Returns:
            AsyncSession: Database session with tenant context set
        """
        self.session = AsyncSessionFactory()
        
        # Set tenant context if provided
        if self.tenant_id:
            await set_tenant_context(self.session, self.tenant_id)
        
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