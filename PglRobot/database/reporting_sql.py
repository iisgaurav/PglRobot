from sqlalchemy import BigInteger, Boolean, select
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class ReportingUserSettings(Base):
    __tablename__ = "user_report_settings"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    should_report: Mapped[bool] = mapped_column(Boolean, default=True)


class ReportingChatSettings(Base):
    __tablename__ = "chat_report_settings"
    
    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    should_report: Mapped[bool] = mapped_column(Boolean, default=True)


async def chat_should_report(chat_id: int) -> bool:
    async for session in get_session():
        result = await session.execute(
            select(ReportingChatSettings).where(ReportingChatSettings.chat_id == chat_id)
        )
        settings = result.scalar_one_or_none()
        return settings.should_report if settings else True
    return True

async def user_should_report(user_id: int) -> bool:
    async for session in get_session():
        result = await session.execute(
            select(ReportingUserSettings).where(ReportingUserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        return settings.should_report if settings else True
    return True

async def set_chat_setting(chat_id: int, setting: bool):
    async for session in get_session():
        result = await session.execute(
            select(ReportingChatSettings).where(ReportingChatSettings.chat_id == chat_id)
        )
        settings = result.scalar_one_or_none()
        if not settings:
            settings = ReportingChatSettings(chat_id=chat_id, should_report=setting)
            session.add(settings)
        else:
            settings.should_report = setting
        await session.commit()

async def set_user_setting(user_id: int, setting: bool):
    async for session in get_session():
        result = await session.execute(
            select(ReportingUserSettings).where(ReportingUserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        if not settings:
            settings = ReportingUserSettings(user_id=user_id, should_report=setting)
            session.add(settings)
        else:
            settings.should_report = setting
        await session.commit()
