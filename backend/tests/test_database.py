from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.database import build_async_engine


async def test_async_database_engine_executes_queries() -> None:
    test_engine = build_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1
    await test_engine.dispose()


def test_neon_pooler_uses_external_pooling_strategy() -> None:
    pooled_url = (
        "postgresql+asyncpg://user:password@ep-example-pooler.ap-southeast-1.aws.neon.tech/mco"
    )

    test_engine = build_async_engine(pooled_url)

    assert isinstance(test_engine.pool, NullPool)
