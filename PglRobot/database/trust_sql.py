from sqlalchemy import BigInteger, Integer, select,  String
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class Trust(Base):
    __tablename__ = "trust_system"
    
    chat_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    trust_score: Mapped[int] = mapped_column(Integer, default=0)


async def add_trust(chat_id: int, user_id: int) -> int:
    async for session in get_session():
        result = await session.execute(
            select(Trust).where((Trust.chat_id == str(chat_id)) & (Trust.user_id == user_id))
        )
        trust_obj = result.scalar_one_or_none()
        
        if trust_obj:
            trust_obj.trust_score += 1
        else:
            trust_obj = Trust(chat_id=str(chat_id), user_id=user_id, trust_score=1)
            session.add(trust_obj)
            
        score = trust_obj.trust_score
        await session.commit()
        return score
    return 0


async def remove_trust(chat_id: int, user_id: int) -> int:
    async for session in get_session():
        result = await session.execute(
            select(Trust).where((Trust.chat_id == str(chat_id)) & (Trust.user_id == user_id))
        )
        trust_obj = result.scalar_one_or_none()
        
        if trust_obj:
            trust_obj.trust_score -= 1
            score = trust_obj.trust_score
            if trust_obj.trust_score <= 0:
                await session.delete(trust_obj)
            await session.commit()
            return score
        return 0
    return 0


async def get_trust(chat_id: int, user_id: int) -> int:
    async for session in get_session():
        result = await session.execute(
            select(Trust).where((Trust.chat_id == str(chat_id)) & (Trust.user_id == user_id))
        )
        trust_obj = result.scalar_one_or_none()
        return trust_obj.trust_score if trust_obj else 0
    return 0
