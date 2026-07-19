from sqlalchemy import BigInteger, select
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class NSFWChats(Base):
    __tablename__ = "nsfw_chats"
    
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


async def is_nsfw(chat_id: int) -> bool:
    async for session in get_session():
        result = await session.execute(select(NSFWChats).where(NSFWChats.chat_id == chat_id))
        return result.scalar_one_or_none() is not None
    return False

async def set_nsfw(chat_id: int):
    async for session in get_session():
        result = await session.execute(select(NSFWChats).where(NSFWChats.chat_id == chat_id))
        nsfw = result.scalar_one_or_none()
        if not nsfw:
            nsfw = NSFWChats(chat_id=chat_id)
            session.add(nsfw)
            await session.commit()

async def rem_nsfw(chat_id: int):
    async for session in get_session():
        result = await session.execute(select(NSFWChats).where(NSFWChats.chat_id == chat_id))
        nsfw = result.scalar_one_or_none()
        if nsfw:
            await session.delete(nsfw)
            await session.commit()
