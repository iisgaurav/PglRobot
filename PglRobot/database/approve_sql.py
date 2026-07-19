from sqlalchemy import BigInteger, String, select
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import BASE, async_session

class Approvals(BASE):
    __tablename__ = "approval"
    
    chat_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)


async def approve(chat_id: int, user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Approvals).where((Approvals.chat_id == str(chat_id)) & (Approvals.user_id == user_id))
        )
        if not result.scalar_one_or_none():
            app = Approvals(chat_id=str(chat_id), user_id=user_id)
            session.add(app)
            await session.commit()

async def disapprove(chat_id: int, user_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Approvals).where((Approvals.chat_id == str(chat_id)) & (Approvals.user_id == user_id))
        )
        app = result.scalar_one_or_none()
        if app:
            await session.delete(app)
            await session.commit()
            return True
        return False

async def is_approved(chat_id: int, user_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Approvals).where((Approvals.chat_id == str(chat_id)) & (Approvals.user_id == user_id))
        )
        return result.scalar_one_or_none() is not None

async def list_approved(chat_id: int) -> list[int]:
    async with async_session() as session:
        result = await session.execute(
            select(Approvals.user_id).where(Approvals.chat_id == str(chat_id))
        )
        return [int(row) for row in result.scalars().all()]
