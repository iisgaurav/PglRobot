from sqlalchemy import BigInteger, UnicodeText, select
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class UserInfo(Base):
    __tablename__ = "userinfo"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    info: Mapped[str] = mapped_column(UnicodeText, nullable=True)

class UserBio(Base):
    __tablename__ = "userbio"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    bio: Mapped[str] = mapped_column(UnicodeText, nullable=True)


async def get_user_info(user_id: int) -> str | None:
    async for session in get_session():
        result = await session.execute(select(UserInfo).where(UserInfo.user_id == user_id))
        info = result.scalar_one_or_none()
        return info.info if info else None

async def set_user_info(user_id: int, info: str):
    async for session in get_session():
        result = await session.execute(select(UserInfo).where(UserInfo.user_id == user_id))
        userinfo = result.scalar_one_or_none()
        if not userinfo:
            userinfo = UserInfo(user_id=user_id, info=info)
            session.add(userinfo)
        else:
            userinfo.info = info
        await session.commit()

async def get_user_bio(user_id: int) -> str | None:
    async for session in get_session():
        result = await session.execute(select(UserBio).where(UserBio.user_id == user_id))
        bio = result.scalar_one_or_none()
        return bio.bio if bio else None

async def set_user_bio(user_id: int, bio: str):
    async for session in get_session():
        result = await session.execute(select(UserBio).where(UserBio.user_id == user_id))
        userbio = result.scalar_one_or_none()
        if not userbio:
            userbio = UserBio(user_id=user_id, bio=bio)
            session.add(userbio)
        else:
            userbio.bio = bio
        await session.commit()
