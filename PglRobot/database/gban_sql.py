from sqlalchemy import BigInteger, String, select
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class GBan(Base):
    __tablename__ = "gbans"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)

async def is_gbanned(user_id: int) -> bool:
    async for session in get_session():
        result = await session.execute(select(GBan).where(GBan.user_id == user_id))
        return result.scalar_one_or_none() is not None
    return False

async def get_gban_reason(user_id: int) -> str | None:
    async for session in get_session():
        result = await session.execute(select(GBan).where(GBan.user_id == user_id))
        gban = result.scalar_one_or_none()
        return gban.reason if gban else None
    return None

async def add_gban(user_id: int, reason: str | None = None):
    async for session in get_session():
        result = await session.execute(select(GBan).where(GBan.user_id == user_id))
        gban = result.scalar_one_or_none()
        if not gban:
            gban = GBan(user_id=user_id, reason=reason)
            session.add(gban)
        else:
            gban.reason = reason
        await session.commit()

async def remove_gban(user_id: int):
    async for session in get_session():
        result = await session.execute(select(GBan).where(GBan.user_id == user_id))
        gban = result.scalar_one_or_none()
        if gban:
            await session.delete(gban)
            await session.commit()

async def get_all_gbans() -> list[int]:
    async for session in get_session():
        result = await session.execute(select(GBan.user_id))
        return [row for row in result.scalars().all()]
    return []
