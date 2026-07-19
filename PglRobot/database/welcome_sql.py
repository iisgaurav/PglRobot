from sqlalchemy import BigInteger, Boolean, String, Integer, select
from sqlalchemy.orm import Mapped, mapped_column

from PglRobot.database.db_core import Base, get_session
import logging
import random

logger = logging.getLogger(__name__)

DEFAULT_WELCOME_MESSAGES = [
    "{first} is here!",
    "Ready player {first}",
    "Genos, {first} is here.",
    "A wild {first} appeared.",
    "{first} came in like a Lion!",
    "{first} has joined your party.",
    "{first} just joined. Can I get a heal?",
    "{first} just joined the chat - asdgfhak!",
    "{first} just joined. Everyone, look busy!",
    "Welcome, {first}. Stay awhile and listen.",
    "Welcome, {first}. We were expecting you ( ͡° ͜ʖ ͡°)",
    "Welcome, {first}. We hope you brought pizza.",
    "Swoooosh. {first} just landed.",
    "Brace yourselves. {first} just joined the chat.",
    "{first} just arrived. Seems OP - please nerf.",
    "{first} just slid into the chat.",
    "A {first} has spawned in the chat.",
    "Big {first} showed up!",
    "Where’s {first}? In the chat!",
    "{first} hopped into the chat. Kangaroo!!",
    "Challenger approaching! {first} has appeared!",
    "It's a bird! It's a plane! Nevermind, it's just {first}.",
    "It's {first}! Praise the sun! \\o/",
    "Ha! {first} has joined! You activated my trap card!",
    "Hey! Listen! {first} has joined!",
    "We've been expecting you {first}",
    "It's dangerous to go alone, take {first}!",
    "{first} has joined the chat! It's super effective!",
    "Cheers, love! {first} is here!",
    "{first} is here, as the prophecy foretold.",
    "{first} has arrived. Party's over.",
    "Hello. Is it {first} you're looking for?",
]

DEFAULT_GOODBYE_MESSAGES = [
    "{first} will be missed.",
    "{first} just went offline.",
    "{first} has left the lobby.",
    "{first} has left the clan.",
    "{first} has left the game.",
    "{first} has fled the area.",
    "{first} is out of the running.",
    "Nice knowing ya, {first}!",
    "It was a fun time {first}.",
    "We hope to see you again soon, {first}.",
    "I donut want to say goodbye, {first}.",
    "Goodbye {first}! Guess who's gonna miss you :')",
    "Goodbye {first}! It's gonna be lonely without ya.",
    "Please don't leave me alone in this place, {first}!",
    "Good luck finding better shit-posters than us, {first}!",
    "You know we're gonna miss you {first}. Right? Right? Right?",
    "Congratulations, {first}! You're officially free of this mess.",
    "{first}. You were an opponent worth fighting.",
    "You're leaving, {first}? Yare Yare Daze.",
]

class WelcomePref(Base):
    __tablename__ = "welcome_pref"
    
    chat_id: Mapped[str] = mapped_column(String, primary_key=True)
    should_welcome: Mapped[bool] = mapped_column(Boolean, default=True)
    should_goodbye: Mapped[bool] = mapped_column(Boolean, default=True)
    clean_welcome: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Store IDs of the previous welcome/goodbye messages for cleaning
    last_welcome_msg_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_goodbye_msg_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    
    welcome_text: Mapped[str | None] = mapped_column(String, nullable=True)
    welcome_media_id: Mapped[str | None] = mapped_column(String, nullable=True)
    welcome_media_type: Mapped[int] = mapped_column(Integer, default=0) # 0: text, 1: photo, 2: video, 3: animation, 4: audio, 5: document
    
    leave_text: Mapped[str | None] = mapped_column(String, nullable=True)
    leave_media_id: Mapped[str | None] = mapped_column(String, nullable=True)
    leave_media_type: Mapped[int] = mapped_column(Integer, default=0)


def get_random_welcome() -> str:
    return random.choice(DEFAULT_WELCOME_MESSAGES)

def get_random_goodbye() -> str:
    return random.choice(DEFAULT_GOODBYE_MESSAGES)

async def _get_pref(chat_id: int, session) -> WelcomePref:
    result = await session.execute(select(WelcomePref).where(WelcomePref.chat_id == str(chat_id)))
    pref = result.scalar_one_or_none()
    if not pref:
        pref = WelcomePref(
            chat_id=str(chat_id),
            should_welcome=True,
            should_goodbye=True,
            clean_welcome=False,
            welcome_text=None,
            leave_text=None,
        )
        session.add(pref)
        await session.commit()
    return pref

async def get_welcome_pref(chat_id: int) -> dict:
    async for session in get_session():
        pref = await _get_pref(chat_id, session)
        return {
            "should_welcome": pref.should_welcome,
            "should_goodbye": pref.should_goodbye,
            "clean_welcome": pref.clean_welcome,
            "welcome_text": pref.welcome_text,
            "welcome_media_id": pref.welcome_media_id,
            "welcome_media_type": pref.welcome_media_type,
            "leave_text": pref.leave_text,
            "leave_media_id": pref.leave_media_id,
            "leave_media_type": pref.leave_media_type,
            "last_welcome_msg_id": pref.last_welcome_msg_id,
            "last_goodbye_msg_id": pref.last_goodbye_msg_id
        }
    return {
        "should_welcome": True,
        "should_goodbye": True,
        "clean_welcome": False,
        "welcome_text": None,
        "welcome_media_id": None,
        "welcome_media_type": 0,
        "leave_text": None,
        "leave_media_id": None,
        "leave_media_type": 0,
        "last_welcome_msg_id": None,
        "last_goodbye_msg_id": None
    }

async def set_welcome_status(chat_id: int, status: bool) -> None:
    async for session in get_session():
        pref = await _get_pref(chat_id, session)
        pref.should_welcome = status
        await session.commit()

async def set_goodbye_status(chat_id: int, status: bool) -> None:
    async for session in get_session():
        pref = await _get_pref(chat_id, session)
        pref.should_goodbye = status
        await session.commit()

async def set_clean_welcome(chat_id: int, status: bool) -> None:
    async for session in get_session():
        pref = await _get_pref(chat_id, session)
        pref.clean_welcome = status
        await session.commit()

async def set_welcome_message(chat_id: int, text: str | None, media_id: str | None, media_type: int) -> None:
    async for session in get_session():
        pref = await _get_pref(chat_id, session)
        pref.welcome_text = text
        pref.welcome_media_id = media_id
        pref.welcome_media_type = media_type
        await session.commit()

async def set_goodbye_message(chat_id: int, text: str | None, media_id: str | None, media_type: int) -> None:
    async for session in get_session():
        pref = await _get_pref(chat_id, session)
        pref.leave_text = text
        pref.leave_media_id = media_id
        pref.leave_media_type = media_type
        await session.commit()

async def set_last_welcome_msg_id(chat_id: int, msg_id: int | None) -> None:
    async for session in get_session():
        pref = await _get_pref(chat_id, session)
        pref.last_welcome_msg_id = msg_id
        await session.commit()

async def set_last_goodbye_msg_id(chat_id: int, msg_id: int | None) -> None:
    async for session in get_session():
        pref = await _get_pref(chat_id, session)
        pref.last_goodbye_msg_id = msg_id
        await session.commit()
