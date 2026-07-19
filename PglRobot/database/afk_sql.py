from sqlalchemy import BigInteger, Boolean, UnicodeText
from sqlalchemy.orm import Mapped, mapped_column

from PglRobot.database.db_core import BASE, async_session

class AFK(BASE):
    __tablename__ = "afk_users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    is_afk: Mapped[bool] = mapped_column(Boolean, default=True)
    reason: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)


async def is_afk(user_id: int) -> bool:
    async with async_session() as session:
        user = await session.get(AFK, user_id)
        return user.is_afk if user else False


async def check_afk_status(user_id: int) -> AFK | None:
    async with async_session() as session:
        return await session.get(AFK, user_id)


async def set_afk(user_id: int, reason: str = "") -> None:
    async with async_session() as session:
        async with session.begin():
            curr = await session.get(AFK, user_id)
            if not curr:
                curr = AFK(user_id=user_id, reason=reason, is_afk=True)
                session.add(curr)
            else:
                curr.is_afk = True
                curr.reason = reason


async def rm_afk(user_id: int) -> bool:
    async with async_session() as session:
        async with session.begin():
            curr = await session.get(AFK, user_id)
            if curr:
                await session.delete(curr)
                return True
            return False


async def toggle_afk(user_id: int, reason: str = "") -> None:
    async with async_session() as session:
        async with session.begin():
            curr = await session.get(AFK, user_id)
            if not curr:
                curr = AFK(user_id=user_id, reason=reason, is_afk=True)
                session.add(curr)
            else:
                curr.is_afk = not curr.is_afk
