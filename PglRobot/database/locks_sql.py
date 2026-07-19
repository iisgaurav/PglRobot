from sqlalchemy import Boolean, select, String
from sqlalchemy.orm import Mapped, mapped_column
from PglRobot.database.db_core import Base, get_session

class Permissions(Base):
    __tablename__ = "permissions"
    
    chat_id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Booleans represent "is this locked", True means it will be deleted
    audio: Mapped[bool] = mapped_column(Boolean, default=False)
    voice: Mapped[bool] = mapped_column(Boolean, default=False)
    contact: Mapped[bool] = mapped_column(Boolean, default=False)
    video: Mapped[bool] = mapped_column(Boolean, default=False)
    document: Mapped[bool] = mapped_column(Boolean, default=False)
    photo: Mapped[bool] = mapped_column(Boolean, default=False)
    sticker: Mapped[bool] = mapped_column(Boolean, default=False)
    gif: Mapped[bool] = mapped_column(Boolean, default=False)
    url: Mapped[bool] = mapped_column(Boolean, default=False)
    bots: Mapped[bool] = mapped_column(Boolean, default=False)
    forward: Mapped[bool] = mapped_column(Boolean, default=False)
    game: Mapped[bool] = mapped_column(Boolean, default=False)
    location: Mapped[bool] = mapped_column(Boolean, default=False)
    rtl: Mapped[bool] = mapped_column(Boolean, default=False)
    button: Mapped[bool] = mapped_column(Boolean, default=False)
    egame: Mapped[bool] = mapped_column(Boolean, default=False)
    inline: Mapped[bool] = mapped_column(Boolean, default=False)


class Restrictions(Base):
    __tablename__ = "restrictions"
    
    chat_id: Mapped[str] = mapped_column(String, primary_key=True)
    messages: Mapped[bool] = mapped_column(Boolean, default=False)
    media: Mapped[bool] = mapped_column(Boolean, default=False)
    other: Mapped[bool] = mapped_column(Boolean, default=False)
    preview: Mapped[bool] = mapped_column(Boolean, default=False)


async def get_locks(chat_id: int) -> Permissions:
    async for session in get_session():
        result = await session.execute(select(Permissions).where(Permissions.chat_id == str(chat_id)))
        perm = result.scalar_one_or_none()
        if not perm:
            perm = Permissions(chat_id=str(chat_id))
            session.add(perm)
            await session.commit()
        return perm
    return Permissions(chat_id=str(chat_id))

async def get_restr(chat_id: int) -> Restrictions:
    async for session in get_session():
        result = await session.execute(select(Restrictions).where(Restrictions.chat_id == str(chat_id)))
        restr = result.scalar_one_or_none()
        if not restr:
            restr = Restrictions(chat_id=str(chat_id))
            session.add(restr)
            await session.commit()
        return restr
    return Restrictions(chat_id=str(chat_id))

async def update_lock(chat_id: int, lock_type: str, locked: bool):
    async for session in get_session():
        result = await session.execute(select(Permissions).where(Permissions.chat_id == str(chat_id)))
        perm = result.scalar_one_or_none()
        if not perm:
            perm = Permissions(chat_id=str(chat_id))
            session.add(perm)
            
        if hasattr(perm, lock_type):
            setattr(perm, lock_type, locked)
            await session.commit()

async def update_restriction(chat_id: int, restr_type: str, locked: bool):
    async for session in get_session():
        result = await session.execute(select(Restrictions).where(Restrictions.chat_id == str(chat_id)))
        restr = result.scalar_one_or_none()
        if not restr:
            restr = Restrictions(chat_id=str(chat_id))
            session.add(restr)
            
        if restr_type == "all":
            restr.messages = locked
            restr.media = locked
            restr.other = locked
            restr.preview = locked
        elif hasattr(restr, restr_type):
            setattr(restr, restr_type, locked)
            
        await session.commit()

async def is_locked(chat_id: int, lock_type: str) -> bool:
    perm = await get_locks(chat_id)
    return getattr(perm, lock_type, False)

async def is_restr_locked(chat_id: int, lock_type: str) -> bool:
    restr = await get_restr(chat_id)
    if lock_type == "all":
        return restr.messages and restr.media and restr.other and restr.preview
    return getattr(restr, lock_type, False)
