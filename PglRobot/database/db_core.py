import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from PglRobot.config import Config

BASE = declarative_base()
Base = BASE # For compatibility

# Must include ssl require for asyncpg PostgreSQL connections on most hosted databases
DB_URI = Config.SQLALCHEMY_DATABASE_URI
if DB_URI.startswith("postgres://"):
    DB_URI = DB_URI.replace("postgres://", "postgresql+asyncpg://", 1)
elif DB_URI.startswith("postgresql://"):
    DB_URI = DB_URI.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "?" in DB_URI:
        DB_URI = DB_URI.split("?", 1)[0]

if "?sslmode=" in DB_URI or "&sslmode=" in DB_URI:
    DB_URI = DB_URI.split("?sslmode=")[0].split("&sslmode=")[0]

engine = create_async_engine(DB_URI, echo=False, pool_pre_ping=True, pool_size=3, max_overflow=5, connect_args={"ssl": "require", "timeout": 120, "command_timeout": 120})
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

logger = logging.getLogger(__name__)

# Generator for dependency injection
async def get_session():
    async with async_session() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(BASE.metadata.create_all)
    logger.info("Successfully connected to the Database Server!")
