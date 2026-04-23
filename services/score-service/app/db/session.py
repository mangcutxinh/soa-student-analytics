"""
Async SQLAlchemy database session
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# In CSV mode use an in-memory SQLite so no Postgres connection is needed at startup.
_db_url = (
    "sqlite+aiosqlite:///:memory:"
    if settings.DATA_MODE == "csv"
    else settings.DATABASE_URL
)
_engine_kwargs: dict = (
    {}
    if settings.DATA_MODE == "csv"
    else {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}
)

engine = create_async_engine(_db_url, echo=settings.DEBUG, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
