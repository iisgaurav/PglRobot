from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.future import select

from PglRobot.database.db_core import BASE, async_session

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class GroupLogs(BASE):
    __tablename__ = "log_channels"

    chat_id: Mapped[str] = mapped_column(String(14), primary_key=True)
    log_channel: Mapped[str] = mapped_column(String(14), nullable=False)


# ---------------------------------------------------------------------------
# In-memory cache — avoids a DB hit on every single moderation action
# ---------------------------------------------------------------------------

CHANNELS: dict[str, str] = {}


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def set_log_channel(chat_id: int | str, log_channel: int | str) -> None:
    """Set or update the log channel for a group."""
    chat_id_str = str(chat_id)
    log_channel_str = str(log_channel)

    async with async_session() as session:
        async with session.begin():
            row = await session.get(GroupLogs, chat_id_str)
            if row:
                row.log_channel = log_channel_str
            else:
                session.add(GroupLogs(chat_id=chat_id_str, log_channel=log_channel_str))

    CHANNELS[chat_id_str] = log_channel_str


async def get_log_channel(chat_id: int | str) -> str | None:
    """Return the log channel ID for a group (from cache)."""
    return CHANNELS.get(str(chat_id))


async def stop_logging(chat_id: int | str) -> str | None:
    """Remove the log channel for a group. Returns old channel ID if existed."""
    chat_id_str = str(chat_id)

    async with async_session() as session:
        async with session.begin():
            row = await session.get(GroupLogs, chat_id_str)
            if not row:
                return None
            old_channel = row.log_channel
            await session.delete(row)

    CHANNELS.pop(chat_id_str, None)
    return old_channel


async def num_log_channels() -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(func.distinct(GroupLogs.chat_id)))
        )
        val = result.scalar()
        return val if val else 0


async def migrate_chat(old_chat_id: int | str, new_chat_id: int | str) -> None:
    old_str = str(old_chat_id)
    new_str = str(new_chat_id)

    async with async_session() as session:
        async with session.begin():
            row = await session.get(GroupLogs, old_str)
            if row:
                row.chat_id = new_str
                if old_str in CHANNELS:
                    CHANNELS[new_str] = CHANNELS.pop(old_str)


# ---------------------------------------------------------------------------
# Startup cache loader — called on bot startup
# ---------------------------------------------------------------------------

async def load_log_channels() -> None:
    """Pre-load all log channel mappings into memory at startup."""
    CHANNELS.clear()
    async with async_session() as session:
        result = await session.execute(select(GroupLogs))
        for row in result.scalars().all():
            CHANNELS[row.chat_id] = row.log_channel
