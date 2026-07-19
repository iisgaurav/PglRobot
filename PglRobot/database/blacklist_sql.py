from sqlalchemy import String, Integer, select
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import BASE, Base, get_session

class BlackListFilters(BASE):
    __tablename__ = "blacklist"
    
    chat_id: Mapped[str] = mapped_column(String, primary_key=True)
    trigger: Mapped[str] = mapped_column(String, primary_key=True)

class BlacklistSettings(Base):
    __tablename__ = "blacklist_settings"
    
    chat_id: Mapped[str] = mapped_column(String, primary_key=True)
    blacklist_type: Mapped[int] = mapped_column(Integer, default=1) # e.g. 1=delete, 2=warn, 3=ban
    value: Mapped[str] = mapped_column(String, nullable=True)


async def add_to_blacklist(chat_id: int, trigger: str):
    async for session in get_session():
        result = await session.execute(
            select(BlackListFilters).where((BlackListFilters.chat_id == str(chat_id)) & (BlackListFilters.trigger == trigger))
        )
        filt = result.scalar_one_or_none()
        if not filt:
            filt = BlackListFilters(chat_id=str(chat_id), trigger=trigger)
            session.add(filt)
            await session.commit()

async def rm_from_blacklist(chat_id: int, trigger: str) -> bool:
    async for session in get_session():
        result = await session.execute(
            select(BlackListFilters).where((BlackListFilters.chat_id == str(chat_id)) & (BlackListFilters.trigger == trigger))
        )
        filt = result.scalar_one_or_none()
        if filt:
            await session.delete(filt)
            await session.commit()
            return True
        return False
    return False

async def get_chat_blacklist(chat_id: int) -> list[str]:
    async for session in get_session():
        result = await session.execute(
            select(BlackListFilters.trigger).where(BlackListFilters.chat_id == str(chat_id))
        )
        return list(result.scalars().all())
    return []

async def set_blacklist_settings(chat_id: int, blacklist_type: int, value: str = "0"):
    async for session in get_session():
        result = await session.execute(
            select(BlacklistSettings).where(BlacklistSettings.chat_id == str(chat_id))
        )
        setting = result.scalar_one_or_none()
        if not setting:
            setting = BlacklistSettings(chat_id=str(chat_id), blacklist_type=blacklist_type, value=value)
            session.add(setting)
        else:
            setting.blacklist_type = blacklist_type
            setting.value = value
        await session.commit()

async def get_blacklist_settings(chat_id: int) -> tuple[int, str]:
    async for session in get_session():
        result = await session.execute(
            select(BlacklistSettings).where(BlacklistSettings.chat_id == str(chat_id))
        )
        setting = result.scalar_one_or_none()
        if setting:
            return setting.blacklist_type, setting.value or "0"
        return 1, "0"
    return 1, "0"
