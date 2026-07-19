# type: ignore

from PglRobot.database.db_core import BASE, async_session
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy import String, UnicodeText, distinct
from sqlalchemy.orm import Mapped, mapped_column

class Rules(BASE):
    __tablename__ = "rules"
    chat_id: Mapped[str] = mapped_column(String(14), primary_key=True)  
    rules: Mapped[str | None] = mapped_column(UnicodeText, default="")  

    def __init__(self, chat_id):
        self.chat_id = chat_id

    def __repr__(self):
        return "<Chat {} rules: {}>".format(self.chat_id, self.rules)





async def set_rules(chat_id: int | str, rules_text: str) -> None:
    async with async_session() as session:
        rules = await session.get(Rules, str(chat_id))
        if not rules:
            rules = Rules(str(chat_id))
        rules.rules = rules_text

        session.add(rules)
        await session.commit()
async def get_rules(chat_id: int | str) -> str:
    async with async_session() as session:
        rules = await session.get(Rules, str(chat_id))
        ret = ""
        if rules:
            ret = rules.rules or ""

        return ret


async def num_chats() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(distinct(Rules.chat_id))))
        return result.scalar_one_or_none() or 0


async def migrate_chat(old_chat_id: int | str, new_chat_id: int | str) -> None:
    async with async_session() as session:
        chat = await session.get(Rules, str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
        await session.commit()
