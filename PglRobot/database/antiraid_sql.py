from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class AntiRaid(Base):
    __tablename__ = "anti_raid"
    
    chat_id: Mapped[str] = mapped_column(String(14), primary_key=True)  
    status: Mapped[bool] = mapped_column(Boolean, default=False) 

    def __init__(self, chat_id, status=False):
        self.chat_id = str(chat_id)
        self.status = status





async def set_antiraid(chat_id: int, status: bool):
    async for session in get_session():
        chat = await session.get(AntiRaid, str(chat_id))
        
        if chat:
            chat.status = status
        else:
            chat = AntiRaid(chat_id, status)
            session.add(chat)
            
        await session.commit()


async def get_antiraid(chat_id: int) -> bool:
    async for session in get_session():
        try:
            chat = await session.get(AntiRaid, str(chat_id))
            if chat:
                return chat.status
            return False
        finally:
            pass  # session closed
    return False
