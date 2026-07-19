from sqlalchemy import BigInteger, Boolean, select
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class NightMode(Base):
    __tablename__ = "nightmode"
    
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

async def set_nightmode(chat_id: int, status: bool):
    async for session in get_session():
        result = await session.execute(select(NightMode).where(NightMode.chat_id == chat_id))
        nm = result.scalar_one_or_none()
        if not nm:
            nm = NightMode(chat_id=chat_id, is_enabled=status)
            session.add(nm)
        else:
            nm.is_enabled = status
        await session.commit()

async def is_nightmode_enabled(chat_id: int) -> bool:
    async for session in get_session():
        result = await session.execute(select(NightMode).where(NightMode.chat_id == chat_id))
        nm = result.scalar_one_or_none()
        return nm.is_enabled if nm else False
    return False

async def get_all_nightmode_chats() -> list[int]:
    async for session in get_session():
        result = await session.execute(select(NightMode).where(NightMode.is_enabled == True))
        return [row.chat_id for row in result.scalars().all()]
    return []
