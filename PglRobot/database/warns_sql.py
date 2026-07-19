import json
from sqlalchemy import BigInteger, String, UnicodeText, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.future import select
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects import postgresql

from PglRobot.database.db_core import BASE, async_session

class ArrayType(TypeDecorator):
    """Custom type to support arrays in Postgres and JSON strings in SQLite."""
    impl = UnicodeText
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.ARRAY(UnicodeText()))
        return dialect.type_descriptor(UnicodeText())

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql':
            return value if value is not None else []
        return json.dumps(value) if value is not None else '[]'

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value if value is not None else []
        return json.loads(value) if value is not None else []


class Warns(BASE):
    __tablename__ = "warns"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chat_id: Mapped[str] = mapped_column(String(14), primary_key=True)
    num_warns: Mapped[int] = mapped_column(Integer, default=0)
    reasons: Mapped[list[str]] = mapped_column(ArrayType, default=list)


class WarnFilters(BASE):
    __tablename__ = "warn_filters"
    
    chat_id: Mapped[str] = mapped_column(String(14), primary_key=True)
    keyword: Mapped[str] = mapped_column(UnicodeText, primary_key=True)
    reply: Mapped[str] = mapped_column(UnicodeText, nullable=False)


class WarnSettings(BASE):
    __tablename__ = "warn_settings"
    
    chat_id: Mapped[str] = mapped_column(String(14), primary_key=True)
    warn_limit: Mapped[int] = mapped_column(Integer, default=3)
    soft_warn: Mapped[bool] = mapped_column(Boolean, default=False)


# Cache for Warn Filters to avoid DB hits on every message
WARN_FILTERS: dict[str, list[str]] = {}


async def warn_user(user_id: int, chat_id: int | str, reason: str | None = None) -> tuple[int, list[str]]:
    chat_id_str = str(chat_id)
    async with async_session() as session:
        async with session.begin():
            warned_user = await session.get(Warns, (user_id, chat_id_str))
            if not warned_user:
                warned_user = Warns(user_id=user_id, chat_id=chat_id_str, num_warns=0, reasons=[])
                session.add(warned_user)

            warned_user.num_warns += 1
            if reason:
                # Force SQLAlchemy to detect array mutation
                current_reasons = list(warned_user.reasons)
                current_reasons.append(reason)
                warned_user.reasons = current_reasons

            num = warned_user.num_warns
            reasons = list(warned_user.reasons)
            return num, reasons


async def remove_warn(user_id: int, chat_id: int | str) -> bool:
    chat_id_str = str(chat_id)
    async with async_session() as session:
        async with session.begin():
            warned_user = await session.get(Warns, (user_id, chat_id_str))
            if warned_user and warned_user.num_warns > 0:
                warned_user.num_warns -= 1
                current_reasons = list(warned_user.reasons)
                if current_reasons:
                    current_reasons.pop()
                warned_user.reasons = current_reasons
                return True
            return False


async def reset_warns(user_id: int, chat_id: int | str) -> None:
    chat_id_str = str(chat_id)
    async with async_session() as session:
        async with session.begin():
            warned_user = await session.get(Warns, (user_id, chat_id_str))
            if warned_user:
                warned_user.num_warns = 0
                warned_user.reasons = []


async def get_warns(user_id: int, chat_id: int | str) -> tuple[int, list[str]] | None:
    chat_id_str = str(chat_id)
    async with async_session() as session:
        user = await session.get(Warns, (user_id, chat_id_str))
        if not user:
            return None
        return user.num_warns, list(user.reasons)


async def add_warn_filter(chat_id: int | str, keyword: str, reply: str) -> None:
    chat_id_str = str(chat_id)
    async with async_session() as session:
        async with session.begin():
            warn_filt = await session.get(WarnFilters, (chat_id_str, keyword))
            if not warn_filt:
                warn_filt = WarnFilters(chat_id=chat_id_str, keyword=keyword, reply=reply)
                session.add(warn_filt)
            else:
                warn_filt.reply = reply

            # Update Cache
            current_filters = WARN_FILTERS.get(chat_id_str, [])
            if keyword not in current_filters:
                current_filters.append(keyword)
                WARN_FILTERS[chat_id_str] = sorted(current_filters, key=lambda x: (-len(x), x))


async def remove_warn_filter(chat_id: int | str, keyword: str) -> bool:
    chat_id_str = str(chat_id)
    async with async_session() as session:
        async with session.begin():
            warn_filt = await session.get(WarnFilters, (chat_id_str, keyword))
            if warn_filt:
                await session.delete(warn_filt)
                # Update Cache
                if chat_id_str in WARN_FILTERS and keyword in WARN_FILTERS[chat_id_str]:
                    WARN_FILTERS[chat_id_str].remove(keyword)
                return True
            return False


async def get_chat_warn_triggers(chat_id: int | str) -> list[str]:
    return WARN_FILTERS.get(str(chat_id), [])


async def get_chat_warn_filters(chat_id: int | str) -> list[WarnFilters]:
    chat_id_str = str(chat_id)
    async with async_session() as session:
        result = await session.execute(select(WarnFilters).filter_by(chat_id=chat_id_str))
        return list(result.scalars().all())


async def get_warn_filter(chat_id: int | str, keyword: str) -> WarnFilters | None:
    async with async_session() as session:
        return await session.get(WarnFilters, (str(chat_id), keyword))


async def set_warn_limit(chat_id: int | str, warn_limit: int) -> None:
    chat_id_str = str(chat_id)
    async with async_session() as session:
        async with session.begin():
            curr_setting = await session.get(WarnSettings, chat_id_str)
            if not curr_setting:
                curr_setting = WarnSettings(chat_id=chat_id_str, warn_limit=warn_limit, soft_warn=False)
                session.add(curr_setting)
            else:
                curr_setting.warn_limit = warn_limit


async def set_warn_strength(chat_id: int | str, soft_warn: bool) -> None:
    chat_id_str = str(chat_id)
    async with async_session() as session:
        async with session.begin():
            curr_setting = await session.get(WarnSettings, chat_id_str)
            if not curr_setting:
                curr_setting = WarnSettings(chat_id=chat_id_str, warn_limit=3, soft_warn=soft_warn)
                session.add(curr_setting)
            else:
                curr_setting.soft_warn = soft_warn


async def get_warn_setting(chat_id: int | str) -> tuple[int, bool]:
    chat_id_str = str(chat_id)
    async with async_session() as session:
        setting = await session.get(WarnSettings, chat_id_str)
        if setting:
            return setting.warn_limit, setting.soft_warn
        return 3, False


async def num_warns() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.sum(Warns.num_warns)))
        val = result.scalar()
        return val if val else 0


async def num_warn_chats() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(func.distinct(Warns.chat_id))))
        val = result.scalar()
        return val if val else 0


async def num_warn_filters() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(WarnFilters.chat_id)))
        val = result.scalar()
        return val if val else 0


async def num_warn_chat_filters(chat_id: int | str) -> int:
    chat_id_str = str(chat_id)
    async with async_session() as session:
        result = await session.execute(select(func.count(WarnFilters.chat_id)).filter_by(chat_id=chat_id_str))
        val = result.scalar()
        return val if val else 0


async def num_warn_filter_chats() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(func.distinct(WarnFilters.chat_id))))
        val = result.scalar()
        return val if val else 0


async def migrate_chat(old_chat_id: int | str, new_chat_id: int | str) -> None:
    old_id = str(old_chat_id)
    new_id = str(new_chat_id)
    async with async_session() as session:
        async with session.begin():
            # Migrate Warns
            chat_notes = await session.execute(select(Warns).filter_by(chat_id=old_id))
            for note in chat_notes.scalars().all():
                note.chat_id = new_id

            # Migrate Filters
            chat_filters = await session.execute(select(WarnFilters).filter_by(chat_id=old_id))
            for filt in chat_filters.scalars().all():
                filt.chat_id = new_id

            # Update Cache
            if old_id in WARN_FILTERS:
                WARN_FILTERS[new_id] = WARN_FILTERS.pop(old_id)

            # Migrate Settings
            chat_settings = await session.execute(select(WarnSettings).filter_by(chat_id=old_id))
            for setting in chat_settings.scalars().all():
                setting.chat_id = new_id


async def load_chat_warn_filters() -> None:
    """Load all warn filters into the WARN_FILTERS cache. Should be called during bot startup."""
    WARN_FILTERS.clear()
    async with async_session() as session:
        all_filters = await session.execute(select(WarnFilters))
        for x in all_filters.scalars().all():
            if x.chat_id not in WARN_FILTERS:
                WARN_FILTERS[x.chat_id] = []
            WARN_FILTERS[x.chat_id].append(x.keyword)

        for chat_id, filters in WARN_FILTERS.items():
            WARN_FILTERS[chat_id] = sorted(set(filters), key=lambda i: (-len(i), i))
