from collections.abc import AsyncIterator
from uuid import uuid4

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import get_settings


def _uses_neon_pooler(database_url: str) -> bool:
    url = make_url(database_url)
    return (
        url.drivername == "postgresql+asyncpg" and url.host is not None and "-pooler." in url.host
    )


def build_async_engine(database_url: str) -> AsyncEngine:
    if _uses_neon_pooler(database_url):
        # Neon already provides transaction pooling via PgBouncer. Avoid stacking
        # SQLAlchemy's connection pool on top and give asyncpg prepared statements
        # unique names so different physical server connections cannot collide.
        return create_async_engine(
            database_url,
            pool_pre_ping=True,
            poolclass=NullPool,
            connect_args={
                "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
            },
        )
    return create_async_engine(database_url, pool_pre_ping=True)


settings = get_settings()
engine = build_async_engine(settings.database_url)
SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
