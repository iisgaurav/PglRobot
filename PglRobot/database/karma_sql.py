from sqlalchemy import BigInteger, Boolean, Integer, select
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class KarmaState(Base):
    __tablename__ = "karma_state"
    
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class KarmaStats(Base):
    __tablename__ = "karma_stats"
    
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    karma: Mapped[int] = mapped_column(Integer, default=0)

async def set_karma_state(chat_id: int, status: bool):
    async for session in get_session():
        result = await session.execute(select(KarmaState).where(KarmaState.chat_id == chat_id))
        ks = result.scalar_one_or_none()
        if not ks:
            ks = KarmaState(chat_id=chat_id, is_enabled=status)
            session.add(ks)
        else:
            ks.is_enabled = status
        await session.commit()

async def is_karma_enabled(chat_id: int) -> bool:
    async for session in get_session():
        result = await session.execute(select(KarmaState).where(KarmaState.chat_id == chat_id))
        ks = result.scalar_one_or_none()
        return ks.is_enabled if ks else True
    return True

async def update_karma(chat_id: int, user_id: int, amount: int) -> int:
    async for session in get_session():
        result = await session.execute(
            select(KarmaStats).where((KarmaStats.chat_id == chat_id) & (KarmaStats.user_id == user_id))
        )
        stats = result.scalar_one_or_none()
        if not stats:
            stats = KarmaStats(chat_id=chat_id, user_id=user_id, karma=amount)
            session.add(stats)
        else:
            stats.karma += amount
        
        new_karma = stats.karma
        await session.commit()
        return new_karma
    return amount

async def get_karma(chat_id: int, user_id: int) -> int:
    async for session in get_session():
        result = await session.execute(
            select(KarmaStats).where((KarmaStats.chat_id == chat_id) & (KarmaStats.user_id == user_id))
        )
        stats = result.scalar_one_or_none()
        return stats.karma if stats else 0
    return 0
