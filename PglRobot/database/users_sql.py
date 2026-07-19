from sqlalchemy import BigInteger, ForeignKey, String, UnicodeText, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.future import select

from PglRobot.database.db_core import BASE, async_session

class Users(BASE):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)

class Chats(BASE):
    __tablename__ = "chats"
    
    chat_id: Mapped[str] = mapped_column(String(14), primary_key=True)
    chat_name: Mapped[str] = mapped_column(UnicodeText, nullable=False)

class ChatMembers(BASE):
    __tablename__ = "chat_members"
    
    priv_chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat: Mapped[str] = mapped_column(String(14), ForeignKey("chats.chat_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    user: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    
    __table_args__ = (UniqueConstraint("chat", "user", name="_chat_members_uc"),)


async def update_user(user_id: int, username: str | None, chat_id: int | str | None = None, chat_name: str | None = None) -> None:
    async with async_session() as session:
        async with session.begin():
            # Update User
            user = await session.get(Users, user_id)
            if not user:
                user = Users(user_id=user_id, username=username)
                session.add(user)
            else:
                    user.username = username

            if not chat_id or not chat_name:
                return

            # Update Chat
            chat_id_str = str(chat_id)
            chat = await session.get(Chats, chat_id_str)
            if not chat:
                chat = Chats(chat_id=chat_id_str, chat_name=chat_name)
                session.add(chat)
            else:
                chat.chat_name = chat_name

            # Update Member
            result = await session.execute(
                select(ChatMembers).filter_by(chat=chat_id_str, user=user_id)
            )
            member = result.scalar_one_or_none()
            if not member:
                member = ChatMembers(chat=chat_id_str, user=user_id)
                session.add(member)


async def num_users() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(Users.user_id)))
        count = result.scalar()
        return count if count is not None else 0


async def num_chats() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(Chats.chat_id)))
        count = result.scalar()
        return count if count is not None else 0

async def get_chat_users(chat_id: str | int) -> list[ChatMembers]:
    async with async_session() as session:
        result = await session.execute(
            select(ChatMembers).filter_by(chat=str(chat_id))
        )
        return list(result.scalars().all())

async def get_all_users() -> list[int]:
    async with async_session() as session:
        result = await session.execute(select(Users.user_id))
        return list(result.scalars().all())

async def get_all_chats() -> list[str]:
    async with async_session() as session:
        result = await session.execute(select(Chats.chat_id))
        return list(result.scalars().all())
