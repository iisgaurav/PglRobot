from enum import IntEnum
from sqlalchemy import BigInteger, Boolean, Integer, String, UnicodeText, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.future import select

from PglRobot.database.db_core import BASE, async_session


# ---------------------------------------------------------------------------
# Message type enum — matches old bot's Types enum values
# ---------------------------------------------------------------------------

class MsgType(IntEnum):
    TEXT       = 1
    BUTTON_TEXT = 2
    STICKER    = 3
    DOCUMENT   = 4
    PHOTO      = 5
    AUDIO      = 6
    VOICE      = 7
    VIDEO      = 8
    VIDEO_NOTE = 9


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Notes(BASE):
    __tablename__ = "notes"

    chat_id: Mapped[str] = mapped_column(String(14), primary_key=True)
    name: Mapped[str] = mapped_column(UnicodeText, primary_key=True)
    value: Mapped[str] = mapped_column(UnicodeText, nullable=False, default="")
    file: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)
    msgtype: Mapped[int] = mapped_column(Integer, default=MsgType.TEXT)


class NoteButtons(BASE):
    __tablename__ = "note_urls"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(String(14), nullable=False)
    note_name: Mapped[str] = mapped_column(UnicodeText, nullable=False)
    name: Mapped[str] = mapped_column(UnicodeText, nullable=False)
    url: Mapped[str] = mapped_column(UnicodeText, nullable=False)
    same_line: Mapped[bool] = mapped_column(Boolean, default=False)


# ---------------------------------------------------------------------------
# CRUD functions
# ---------------------------------------------------------------------------

async def add_note(
    chat_id: int | str,
    name: str,
    value: str,
    msgtype: MsgType,
    file: str | None = None,
    buttons: list[tuple[str, str, bool]] | None = None,
) -> None:
    """Save or overwrite a note and its buttons."""
    chat_id_str = str(chat_id)
    name = name.lower()

    async with async_session() as session:
        async with session.begin():
            # Remove existing note + its buttons first
            existing = await session.get(Notes, (chat_id_str, name))
            if existing:
                old_btns = await session.execute(
                    select(NoteButtons).filter_by(chat_id=chat_id_str, note_name=name)
                )
                for btn in old_btns.scalars().all():
                    await session.delete(btn)
                await session.delete(existing)

            # Add fresh note
            note = Notes(
                chat_id=chat_id_str,
                name=name,
                value=value or "",
                msgtype=int(msgtype),
                file=file,
            )
            session.add(note)

            # Add buttons
            if buttons:
                for btn_name, url, same_line in buttons:
                    session.add(NoteButtons(
                        chat_id=chat_id_str,
                        note_name=name,
                        name=btn_name,
                        url=url,
                        same_line=same_line,
                    ))


async def get_note(chat_id: int | str, name: str) -> Notes | None:
    """Fetch a note by name (case-insensitive)."""
    async with async_session() as session:
        return await session.get(Notes, (str(chat_id), name.lower()))


async def get_note_buttons(chat_id: int | str, name: str) -> list[NoteButtons]:
    """Fetch all inline buttons for a note, ordered by insertion."""
    async with async_session() as session:
        result = await session.execute(
            select(NoteButtons)
            .filter_by(chat_id=str(chat_id), note_name=name.lower())
            .order_by(NoteButtons.id)
        )
        return list(result.scalars().all())


async def rm_note(chat_id: int | str, name: str) -> bool:
    """Delete a note and its buttons. Returns True if it existed."""
    chat_id_str = str(chat_id)
    name = name.lower()

    async with async_session() as session:
        async with session.begin():
            note = await session.get(Notes, (chat_id_str, name))
            if not note:
                return False

            btns = await session.execute(
                select(NoteButtons).filter_by(chat_id=chat_id_str, note_name=name)
            )
            for btn in btns.scalars().all():
                await session.delete(btn)

            await session.delete(note)
            return True


async def rm_all_notes(chat_id: int | str) -> None:
    """Delete all notes and their buttons for a chat."""
    chat_id_str = str(chat_id)

    async with async_session() as session:
        async with session.begin():
            notes = await session.execute(select(Notes).filter_by(chat_id=chat_id_str))
            for note in notes.scalars().all():
                btns = await session.execute(
                    select(NoteButtons).filter_by(chat_id=chat_id_str, note_name=note.name)
                )
                for btn in btns.scalars().all():
                    await session.delete(btn)
                await session.delete(note)


async def get_all_chat_notes(chat_id: int | str) -> list[Notes]:
    """Return all notes for a chat, sorted alphabetically."""
    async with async_session() as session:
        result = await session.execute(
            select(Notes)
            .filter_by(chat_id=str(chat_id))
            .order_by(Notes.name.asc())
        )
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

async def num_notes() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(Notes.name)))
        val = result.scalar()
        return val if val else 0


async def num_note_chats() -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(func.distinct(Notes.chat_id)))
        )
        val = result.scalar()
        return val if val else 0


# ---------------------------------------------------------------------------
# Migration (supergroup upgrade)
# ---------------------------------------------------------------------------

async def migrate_chat(old_chat_id: int | str, new_chat_id: int | str) -> None:
    old_id = str(old_chat_id)
    new_id = str(new_chat_id)

    async with async_session() as session:
        async with session.begin():
            notes = await session.execute(select(Notes).filter_by(chat_id=old_id))
            for note in notes.scalars().all():
                note.chat_id = new_id

            btns = await session.execute(select(NoteButtons).filter_by(chat_id=old_id))
            for btn in btns.scalars().all():
                btn.chat_id = new_id
