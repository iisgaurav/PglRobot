from sqlalchemy import BigInteger, Boolean, String, Integer, UnicodeText, select, delete
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session
import time

class ChatAccessConnectionSettings(Base):
    __tablename__ = "access_connection"
    
    chat_id: Mapped[str] = mapped_column(String, primary_key=True)
    allow_connect_to_chat: Mapped[bool] = mapped_column(Boolean, default=True)


class Connection(Base):
    __tablename__ = "connection"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chat_id: Mapped[str | None] = mapped_column(String, nullable=True)


class ConnectionHistory(Base):
    __tablename__ = "connection_history"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chat_id: Mapped[str] = mapped_column(String, primary_key=True)
    chat_name: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)
    conn_time: Mapped[int] = mapped_column(Integer, default=lambda: int(time.time()))


async def allow_connect_to_chat(chat_id: int) -> bool:
    async for session in get_session():
        result = await session.execute(
            select(ChatAccessConnectionSettings).where(ChatAccessConnectionSettings.chat_id == str(chat_id))
        )
        settings = result.scalar_one_or_none()
        return settings.allow_connect_to_chat if settings else True
    return True

async def set_allow_connect_to_chat(chat_id: int, setting: bool):
    async for session in get_session():
        result = await session.execute(
            select(ChatAccessConnectionSettings).where(ChatAccessConnectionSettings.chat_id == str(chat_id))
        )
        settings = result.scalar_one_or_none()
        if not settings:
            settings = ChatAccessConnectionSettings(chat_id=str(chat_id), allow_connect_to_chat=setting)
            session.add(settings)
        else:
            settings.allow_connect_to_chat = setting
        await session.commit()


async def connect(user_id: int, chat_id: int):
    async for session in get_session():
        result = await session.execute(select(Connection).where(Connection.user_id == user_id))
        conn = result.scalar_one_or_none()
        if not conn:
            conn = Connection(user_id=user_id, chat_id=str(chat_id))
            session.add(conn)
        else:
            conn.chat_id = str(chat_id)
        await session.commit()


async def disconnect(user_id: int) -> bool:
    async for session in get_session():
        result = await session.execute(select(Connection).where(Connection.user_id == user_id))
        conn = result.scalar_one_or_none()
        if conn:
            await session.delete(conn)
            await session.commit()
            return True
        return False
    return False


async def get_connected_chat(user_id: int) -> int | None:
    async for session in get_session():
        result = await session.execute(select(Connection).where(Connection.user_id == user_id))
        conn = result.scalar_one_or_none()
        return int(conn.chat_id) if conn and conn.chat_id else None
    return None


async def add_history(user_id: int, chat_id: int, chat_name: str):
    async for session in get_session():
        result = await session.execute(
            select(ConnectionHistory).where((ConnectionHistory.user_id == user_id) & (ConnectionHistory.chat_id == str(chat_id)))
        )
        hist = result.scalar_one_or_none()
        if not hist:
            hist = ConnectionHistory(user_id=user_id, chat_id=str(chat_id), chat_name=chat_name)
            session.add(hist)
        else:
            hist.chat_name = chat_name
            hist.conn_time = int(time.time())
        await session.commit()


async def get_history(user_id: int) -> list[ConnectionHistory]:
    async for session in get_session():
        result = await session.execute(
            select(ConnectionHistory).where(ConnectionHistory.user_id == user_id).order_by(ConnectionHistory.conn_time.desc())
        )
        return list(result.scalars().all())
    return []

async def clear_history(user_id: int):
    async for session in get_session():
        await session.execute(delete(ConnectionHistory).where(ConnectionHistory.user_id == user_id))
        await session.commit()
