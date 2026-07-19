from sqlalchemy import String, UnicodeText, Boolean, Integer, select
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class CustomFilters(Base):
    __tablename__ = "cust_filters"
    
    chat_id: Mapped[str] = mapped_column(String, primary_key=True)
    keyword: Mapped[str] = mapped_column(UnicodeText, primary_key=True)
    
    # Modern fields
    reply_text: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)
    file_type: Mapped[int] = mapped_column(Integer, default=1) # 1=text, 2=photo, 3=video, 4=audio, 5=voice, 6=document, 7=sticker, 8=animation
    file_id: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)
    
    # Legacy fields (kept for backward compatibility during potential migrations)
    reply: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)
    is_sticker: Mapped[bool] = mapped_column(Boolean, default=False)
    is_document: Mapped[bool] = mapped_column(Boolean, default=False)
    is_image: Mapped[bool] = mapped_column(Boolean, default=False)
    is_audio: Mapped[bool] = mapped_column(Boolean, default=False)
    is_voice: Mapped[bool] = mapped_column(Boolean, default=False)
    is_video: Mapped[bool] = mapped_column(Boolean, default=False)
    has_buttons: Mapped[bool] = mapped_column(Boolean, default=False)


async def add_filter(chat_id: int, keyword: str, reply_text: str | None, file_type: int = 1, file_id: str | None = None, has_buttons: bool = False):
    async for session in get_session():
        result = await session.execute(
            select(CustomFilters).where((CustomFilters.chat_id == str(chat_id)) & (CustomFilters.keyword == keyword))
        )
        filt = result.scalar_one_or_none()
        
        if not filt:
            filt = CustomFilters(
                chat_id=str(chat_id),
                keyword=keyword,
                reply_text=reply_text,
                file_type=file_type,
                file_id=file_id,
                has_buttons=has_buttons
            )
            session.add(filt)
        else:
            filt.reply_text = reply_text
            filt.file_type = file_type
            filt.file_id = file_id
            filt.has_buttons = has_buttons
            
        await session.commit()

async def remove_filter(chat_id: int, keyword: str) -> bool:
    async for session in get_session():
        result = await session.execute(
            select(CustomFilters).where((CustomFilters.chat_id == str(chat_id)) & (CustomFilters.keyword == keyword))
        )
        filt = result.scalar_one_or_none()
        if filt:
            await session.delete(filt)
            await session.commit()
            return True
        return False
    return False

async def get_all_filters(chat_id: int) -> list[CustomFilters]:
    async for session in get_session():
        result = await session.execute(
            select(CustomFilters).where(CustomFilters.chat_id == str(chat_id))
        )
        return list(result.scalars().all())
    return []

async def get_filter(chat_id: int, keyword: str) -> CustomFilters | None:
    async for session in get_session():
        result = await session.execute(
            select(CustomFilters).where((CustomFilters.chat_id == str(chat_id)) & (CustomFilters.keyword == keyword))
        )
        return result.scalar_one_or_none()
    return None
