from sqlalchemy import BigInteger, Boolean, select
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class JoinRequest(Base):
    __tablename__ = "join_requests"
    
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    auto_approve: Mapped[bool] = mapped_column(Boolean, default=False)


async def set_auto_approve(chat_id: int, status: bool):
    async for session in get_session():
        result = await session.execute(select(JoinRequest).where(JoinRequest.chat_id == chat_id))
        req = result.scalar_one_or_none()
        if not req:
            req = JoinRequest(chat_id=chat_id, auto_approve=status)
            session.add(req)
        else:
            req.auto_approve = status
        await session.commit()

async def get_auto_approve(chat_id: int) -> bool:
    async for session in get_session():
        result = await session.execute(select(JoinRequest).where(JoinRequest.chat_id == chat_id))
        req = result.scalar_one_or_none()
        return req.auto_approve if req else False
    return False
