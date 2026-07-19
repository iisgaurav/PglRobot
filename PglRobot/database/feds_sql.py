import uuid
from sqlalchemy import BigInteger, String, select, delete
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class Fed(Base):
    __tablename__ = "feds"
    
    fed_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fed_name: Mapped[str] = mapped_column(String(255))
    owner_id: Mapped[str] = mapped_column(String)

class FedChat(Base):
    __tablename__ = "fed_chats"
    
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    fed_id: Mapped[str] = mapped_column(String(36))

class FedBan(Base):
    __tablename__ = "fed_bans"
    
    fed_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    banned_by: Mapped[int] = mapped_column(BigInteger)


async def create_fed(fed_name: str, owner_id: int) -> str:
    async for session in get_session():
        fed = Fed(fed_name=fed_name, owner_id=str(owner_id))
        session.add(fed)
        await session.commit()
        return fed.fed_id
    return ""

async def get_fed(fed_id: str) -> Fed | None:
    async for session in get_session():
        result = await session.execute(select(Fed).where(Fed.fed_id == fed_id))
        return result.scalar_one_or_none()
    return None

async def get_fed_by_chat(chat_id: int) -> str | None:
    async for session in get_session():
        result = await session.execute(select(FedChat).where(FedChat.chat_id == chat_id))
        fed_chat = result.scalar_one_or_none()
        return fed_chat.fed_id if fed_chat else None
    return None

async def join_fed(chat_id: int, fed_id: str):
    async for session in get_session():
        # First leave any existing fed
        await session.execute(delete(FedChat).where(FedChat.chat_id == chat_id))
        fc = FedChat(chat_id=chat_id, fed_id=fed_id)
        session.add(fc)
        await session.commit()

async def leave_fed(chat_id: int):
    async for session in get_session():
        await session.execute(delete(FedChat).where(FedChat.chat_id == chat_id))
        await session.commit()

async def add_fban(fed_id: str, user_id: int, banned_by: int, reason: str | None = None):
    async for session in get_session():
        result = await session.execute(
            select(FedBan).where((FedBan.fed_id == fed_id) & (FedBan.user_id == user_id))
        )
        fb = result.scalar_one_or_none()
        if not fb:
            fb = FedBan(fed_id=fed_id, user_id=user_id, banned_by=banned_by, reason=reason)
            session.add(fb)
        else:
            fb.reason = reason
        await session.commit()

async def remove_fban(fed_id: str, user_id: int):
    async for session in get_session():
        await session.execute(
            delete(FedBan).where((FedBan.fed_id == fed_id) & (FedBan.user_id == user_id))
        )
        await session.commit()

async def is_fbanned(fed_id: str, user_id: int) -> bool:
    async for session in get_session():
        result = await session.execute(
            select(FedBan).where((FedBan.fed_id == fed_id) & (FedBan.user_id == user_id))
        )
        return result.scalar_one_or_none() is not None
    return False

async def get_fban(fed_id: str, user_id: int) -> FedBan | None:
    async for session in get_session():
        result = await session.execute(
            select(FedBan).where((FedBan.fed_id == fed_id) & (FedBan.user_id == user_id))
        )
        return result.scalar_one_or_none()
    return None
