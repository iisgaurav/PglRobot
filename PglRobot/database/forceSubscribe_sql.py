from sqlalchemy import BigInteger, String, select
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class ForceSubscribe(Base):
    __tablename__ = "forceSubscribe"
    
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel: Mapped[str | None] = mapped_column(String, nullable=True)


async def get_fsub(chat_id: int) -> str | None:
    async for session in get_session():
        result = await session.execute(select(ForceSubscribe).where(ForceSubscribe.chat_id == chat_id))
        fsub = result.scalar_one_or_none()
        return fsub.channel if fsub else None
    return None

async def set_fsub(chat_id: int, channel: str):
    async for session in get_session():
        result = await session.execute(select(ForceSubscribe).where(ForceSubscribe.chat_id == chat_id))
        fsub = result.scalar_one_or_none()
        if not fsub:
            fsub = ForceSubscribe(chat_id=chat_id, channel=channel)
            session.add(fsub)
        else:
            fsub.channel = channel
        await session.commit()

async def remove_fsub(chat_id: int) -> bool:
    async for session in get_session():
        result = await session.execute(select(ForceSubscribe).where(ForceSubscribe.chat_id == chat_id))
        fsub = result.scalar_one_or_none()
        if fsub:
            await session.delete(fsub)
            await session.commit()
            return True
        return False
    return False
