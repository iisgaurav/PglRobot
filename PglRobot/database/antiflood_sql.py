from sqlalchemy import BigInteger, String, Integer, UnicodeText
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.future import select

from PglRobot.database.db_core import Base, get_session

DEF_COUNT = 1
DEF_LIMIT = 0
DEF_OBJ = (None, DEF_COUNT, DEF_LIMIT)


class FloodControl(Base):
    __tablename__ = "antiflood"

    chat_id: Mapped[str] = mapped_column(String(14), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    count: Mapped[int] = mapped_column(Integer, default=DEF_COUNT)
    limit: Mapped[int] = mapped_column(Integer, default=DEF_LIMIT)

    def __init__(self, chat_id: str | int):
        self.chat_id = str(chat_id)  # ensure string

    def __repr__(self) -> str:
        return f"<flood control for {self.chat_id}>"


class FloodSettings(Base):
    __tablename__ = "antiflood_settings"

    chat_id: Mapped[str] = mapped_column(String(14), primary_key=True)
    flood_type: Mapped[int] = mapped_column(Integer, default=1)
    value: Mapped[str] = mapped_column(UnicodeText, default="0")

    def __init__(self, chat_id: str | int, flood_type: int = 1, value: str = "0"):
        self.chat_id = str(chat_id)
        self.flood_type = flood_type
        self.value = value

    def __repr__(self) -> str:
        return f"<{self.chat_id} will executing {self.flood_type} for flood.>"


CHAT_FLOOD: dict[str, tuple[int | None, int, int]] = {}


async def set_flood(chat_id: str | int, amount: int) -> None:
    async for session in get_session():
        flood = await session.get(FloodControl, str(chat_id))
        if not flood:
            flood = FloodControl(str(chat_id))

        flood.user_id = None
        flood.limit = amount

        CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, amount)

        session.add(flood)
        await session.commit()


async def update_flood(chat_id: str | int, user_id: int | None) -> bool:
    if str(chat_id) in CHAT_FLOOD:
        curr_user_id, count, limit = CHAT_FLOOD.get(str(chat_id), DEF_OBJ)

        if limit == 0: 
            return False

        if user_id != curr_user_id or user_id is None:  # other user
            CHAT_FLOOD[str(chat_id)] = (user_id, DEF_COUNT, limit)
            return False

        count = (count or 0) + 1
        if count > limit:  # too many msgs, kick
            CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, limit)
            return True

        # default -> update
        CHAT_FLOOD[str(chat_id)] = (user_id, count, limit)
        return False
    return False


async def get_flood_limit(chat_id: str | int) -> int:
    return CHAT_FLOOD.get(str(chat_id), DEF_OBJ)[2]


async def set_flood_strength(chat_id: str | int, flood_type: int, value: str) -> None:
    async for session in get_session():
        # for flood_type
        # 1 = ban
        # 2 = kick
        # 3 = mute
        # 4 = tban
        # 5 = tmute
        curr_setting = await session.get(FloodSettings, str(chat_id))
        if not curr_setting:
            curr_setting = FloodSettings(
                chat_id, flood_type=int(flood_type), value=value
            )

        curr_setting.flood_type = int(flood_type)
        curr_setting.value = str(value)

        session.add(curr_setting)
        await session.commit()


async def get_flood_setting(chat_id: str | int) -> tuple[int, str]:
    async for session in get_session():
        setting = await session.get(FloodSettings, str(chat_id))
        if setting:
            return setting.flood_type, setting.value
        return 1, "0"
    return 1, "0"


async def migrate_chat(old_chat_id: str | int, new_chat_id: str | int) -> None:
    async for session in get_session():
        flood = await session.get(FloodControl, str(old_chat_id))
        if flood:
            CHAT_FLOOD[str(new_chat_id)] = CHAT_FLOOD.get(str(old_chat_id), DEF_OBJ)
            flood.chat_id = str(new_chat_id)
            await session.commit()


async def load_flood_settings() -> None:
    async for session in get_session():
        global CHAT_FLOOD
        all_chats = (await session.execute(select(FloodControl))).scalars().all()
        CHAT_FLOOD = {chat.chat_id: (None, DEF_COUNT, chat.limit) for chat in all_chats}
