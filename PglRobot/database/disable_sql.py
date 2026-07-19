from PglRobot.database.db_core import Base, get_session
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy import String, UnicodeText, distinct
from sqlalchemy.orm import Mapped, mapped_column


class Disable(Base):
    __tablename__ = "disabled_commands"
    chat_id: Mapped[str] = mapped_column(String(14), primary_key=True)  
    command: Mapped[str] = mapped_column(UnicodeText, primary_key=True)

    def __init__(self, chat_id, command):
        self.chat_id = chat_id
        self.command = command

    def __repr__(self):
        return "Disabled cmd {} in {}".format(self.command, self.chat_id)



DISABLED = {}


async def disable_command(chat_id, disable):
    async for session in get_session():
        disabled = await session.get(Disable, (str(chat_id), disable))

        if not disabled:
            DISABLED.setdefault(str(chat_id), set()).add(disable)

            disabled = Disable(str(chat_id), disable)
            session.add(disabled)
            await session.commit()
            return True

        pass  # session closed
        return False


async def enable_command(chat_id, enable):
    async for session in get_session():
        disabled = await session.get(Disable, (str(chat_id), enable))

        if disabled:
            if enable in DISABLED.get(str(chat_id)):  # sanity check
                DISABLED.setdefault(str(chat_id), set()).remove(enable)

            await session.delete(disabled)
            await session.commit()
            return True

        pass  # session closed
        return False


async def is_command_disabled(chat_id, cmd):
    return str(cmd).lower() in DISABLED.get(str(chat_id), set())


async def get_all_disabled(chat_id):
    return DISABLED.get(str(chat_id), set())


async def num_chats():
    async for session in get_session():
        try:
            return (await session.execute(select(func.count(distinct(Disable.chat_id))))).scalar()
        finally:
            pass  # session closed


async def num_disabled():
    async for session in get_session():
        try:
            return (await session.execute(select(func.count()).select_from(Disable))).scalar()
        finally:
            pass  # session closed


async def migrate_chat(old_chat_id, new_chat_id):
    async for session in get_session():
        chats = (await session.execute(select(Disable).filter(Disable.chat_id == str(old_chat_id)))).scalars().all()
        for chat in chats:
            chat.chat_id = str(new_chat_id)
            session.add(chat)

        if str(old_chat_id) in DISABLED:
            DISABLED[str(new_chat_id)] = DISABLED.get(str(old_chat_id), set())

        await session.commit()


async def load_disabled_commands():
    async for session in get_session():
        global DISABLED
        try:
            all_chats = (await session.execute(select(Disable))).scalars().all()
            for chat in all_chats:
                DISABLED.setdefault(chat.chat_id, set()).add(chat.command)

        finally:
            pass  # session closed


# __load_disabled_commands()
