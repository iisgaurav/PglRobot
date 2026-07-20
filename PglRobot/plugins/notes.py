# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import re
import html
import random
import logging

from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

from PglRobot.utils.admin_filters import IsAdmin
from PglRobot.database import notes_sql as sql
from PglRobot.database.notes_sql import MsgType

logger = logging.getLogger(__name__)
notes_router = Router()

ADMIN_OR_OWNER = IsAdmin("can_change_info")

# ---------------------------------------------------------------------------
# Button URL parser
# Syntax: [Button Label](buttonurl:https://url)
# Same-line: [Btn1](buttonurl:url:same) [Btn2](buttonurl:url)
# ---------------------------------------------------------------------------

BTN_URL_REGEX = re.compile(r'\[([^\[\]]+?)\]\(buttonurl:((?:https?://)[^\)]+?)(:same)?\)')


def parse_buttons(text: str) -> tuple[str, list[tuple[str, str, bool]]]:
    """Strip button definitions from text, return (clean_text, buttons_list)."""
    buttons: list[tuple[str, str, bool]] = []

    def repl(m: re.Match) -> str:
        buttons.append((m.group(1).strip(), m.group(2).strip(), bool(m.group(3))))
        return ""

    clean = BTN_URL_REGEX.sub(repl, text).strip()
    return clean, buttons


def build_keyboard(buttons: list) -> InlineKeyboardMarkup | None:
    """Convert list of NoteButtons DB objects to InlineKeyboardMarkup."""
    if not buttons:
        return None
    keyboard: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for btn in buttons:
        row.append(InlineKeyboardButton(text=btn.name, url=btn.url))
        if not btn.same_line:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ---------------------------------------------------------------------------
# Note type detection from a /save message
# ---------------------------------------------------------------------------

def detect_note_content(message: Message) -> tuple[str | None, str, MsgType, str | None, list]:
    """
    Parse a /save command and return:
    (note_name, text, msgtype, file_id, buttons)
    """
    raw_args = message.text.split(None, 2) if message.text else []
    note_name = raw_args[1].lower() if len(raw_args) >= 2 else None

    reply = message.reply_to_message

    if reply:
        # Saving from a replied message
        if reply.sticker:
            return note_name, "", MsgType.STICKER, reply.sticker.file_id, []

        if reply.video_note:
            return note_name, "", MsgType.VIDEO_NOTE, reply.video_note.file_id, []

        caption = reply.caption or reply.text or ""
        clean, btns = parse_buttons(caption)

        if reply.document:
            return note_name, clean, MsgType.DOCUMENT, reply.document.file_id, btns
        if reply.photo:
            return note_name, clean, MsgType.PHOTO, reply.photo[-1].file_id, btns
        if reply.audio:
            return note_name, clean, MsgType.AUDIO, reply.audio.file_id, btns
        if reply.voice:
            return note_name, clean, MsgType.VOICE, reply.voice.file_id, btns
        if reply.video:
            return note_name, clean, MsgType.VIDEO, reply.video.file_id, btns

        # Plain text reply
        msgtype = MsgType.BUTTON_TEXT if btns else MsgType.TEXT
        return note_name, clean, msgtype, None, btns

    else:
        # Saving inline text from the command itself
        inline_text = raw_args[2] if len(raw_args) >= 3 else ""
        clean, btns = parse_buttons(inline_text)
        msgtype = MsgType.BUTTON_TEXT if btns else MsgType.TEXT
        return note_name, clean, msgtype, None, btns


# ---------------------------------------------------------------------------
# Note sender
# ---------------------------------------------------------------------------

async def send_note(message: Message, chat_id: int, notename: str, show_none: bool = True) -> None:
    note = await sql.get_note(chat_id, notename)
    if not note:
        if show_none:
            await message.reply(
                f"❌ Note <code>#{html.escape(notename)}</code> doesn't exist!",
                parse_mode=ParseMode.HTML,
            )
        return

    buttons = await sql.get_note_buttons(chat_id, notename)
    keyboard = build_keyboard(buttons)

    # Handle %%% random responses
    text = note.value
    if "%%%" in text:
        choices = [c.strip() for c in text.split("%%%") if c.strip()]
        text = random.choice(choices) if choices else text

    msgtype = MsgType(note.msgtype)

    try:
        file_id = str(note.file) if note.file else None
        
        if msgtype == MsgType.STICKER:
            if file_id:
                await message.reply_sticker(file_id)

        elif msgtype == MsgType.DOCUMENT:
            if file_id:
                await message.reply_document(
                    file_id, caption=text or None,
                    parse_mode=ParseMode.HTML, reply_markup=keyboard
                )
        elif msgtype == MsgType.PHOTO:
            if file_id:
                await message.reply_photo(
                    file_id, caption=text or None,
                    parse_mode=ParseMode.HTML, reply_markup=keyboard
                )
        elif msgtype == MsgType.AUDIO:
            if file_id:
                await message.reply_audio(
                    file_id, caption=text or None,
                    parse_mode=ParseMode.HTML, reply_markup=keyboard
                )
        elif msgtype == MsgType.VOICE:
            if file_id:
                await message.reply_voice(
                    file_id, caption=text or None,
                    parse_mode=ParseMode.HTML, reply_markup=keyboard
                )
        elif msgtype == MsgType.VIDEO:
            if file_id:
                await message.reply_video(
                    file_id, caption=text or None,
                    parse_mode=ParseMode.HTML, reply_markup=keyboard
                )
        elif msgtype == MsgType.VIDEO_NOTE:
            if file_id:
                await message.reply_video_note(file_id)

        else:
            # TEXT or BUTTON_TEXT
            await message.reply(
                text or f"<code>#{html.escape(notename)}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )

    except TelegramBadRequest as e:
        logger.error("Failed to send note %s: %s", notename, e)
        await message.reply(f"⚠️ Failed to send note <code>#{html.escape(notename)}</code>.", parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------
# PM fallback
# ---------------------------------------------------------------------------

@notes_router.message(
    Command("save", "get", "notes", "saved", "clear", "removeallnotes"),
    F.chat.type == "private",
)
async def notes_pm_fallback(message: Message):
    await message.reply("This command can only be used in groups.")


# ---------------------------------------------------------------------------
# /save
# ---------------------------------------------------------------------------

@notes_router.message(
    Command("save"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
)
async def save_note(message: Message):
    note_name, text, msgtype, file_id, buttons = detect_note_content(message)

    if not note_name:
        return await message.reply(
            "Usage:\n" +
            "• <code>/save notename text</code>\n" +
            "• Reply to a message: <code>/save notename</code>",
            parse_mode=ParseMode.HTML,
        )

    await sql.add_note(
        message.chat.id, note_name, text, msgtype,
        file=file_id, buttons=buttons
    )
    await message.reply(
        f"✅ Saved note <code>#{note_name}</code>!\n" +
        f"Get it with /get <code>{note_name}</code> or type <code>#{note_name}</code>.",
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------------------------
# /get <notename>
# ---------------------------------------------------------------------------

@notes_router.message(
    Command("get"),
    F.chat.type.in_({"group", "supergroup"}),
)
async def get_note_cmd(message: Message, command: CommandObject):
    if not command.args:
        return await message.reply("Usage: /get <notename>")
    notename = command.args.split()[0].lower()
    await send_note(message, message.chat.id, notename)


# ---------------------------------------------------------------------------
# #notename trigger
# ---------------------------------------------------------------------------

@notes_router.message(
    F.text.regexp(r"^#(\w+)"),
    F.chat.type.in_({"group", "supergroup"}),
)
async def hash_get(message: Message):
    notename = message.text.split()[0][1:].lower()
    if not notename:
        return
    await send_note(message, message.chat.id, notename, show_none=False)


# ---------------------------------------------------------------------------
# /notes or /saved — list all notes
# ---------------------------------------------------------------------------

@notes_router.message(
    Command("notes", "saved"),
    F.chat.type.in_({"group", "supergroup"}),
)
async def list_notes(message: Message):
    notes = await sql.get_all_chat_notes(message.chat.id)
    if not notes:
        return await message.reply("📋 No notes saved in this chat yet!\nAdmins can add notes with /save.")

    lines = "\n".join(f"  • <code>#{n.name}</code>" for n in notes)
    await message.reply(
        f"📋 <b>Notes in {message.chat.title}:</b>\n\n" +
        f"{lines}\n\n" +
        f"<i>Get a note: /get notename  or  #notename</i>",
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------------------------
# /clear <notename>
# ---------------------------------------------------------------------------

@notes_router.message(
    Command("clear"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
)
async def clear_note(message: Message, command: CommandObject):
    if not command.args:
        return await message.reply("Usage: /clear <notename>")

    notename = command.args.split()[0].lower()
    removed = await sql.rm_note(message.chat.id, notename)

    if removed:
        await message.reply(
            f"🗑️ Note <code>#{html.escape(notename)}</code> deleted.", parse_mode=ParseMode.HTML
        )
    else:
        await message.reply(
            f"❌ No note named <code>#{html.escape(notename)}</code> found.", parse_mode=ParseMode.HTML
        )


# ---------------------------------------------------------------------------
# /removeallnotes — owner only, with confirmation button
# ---------------------------------------------------------------------------

@notes_router.message(
    Command("removeallnotes"),
    F.chat.type.in_({"group", "supergroup"}),
)
async def remove_all_notes(message: Message):
    member = await message.chat.get_member(message.from_user.id)
    if member.status != "creator":
        return await message.reply("⚠️ Only the group owner can remove all notes!")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Yes, delete all", callback_data=f"notes:rmall:{message.chat.id}"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="notes:cancel"),
    ]])

    await message.reply(
        f"⚠️ Are you sure you want to delete <b>ALL notes</b> in <b>{message.chat.title}</b>?\n<i>This action cannot be undone!</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


@notes_router.callback_query(F.data.startswith("notes:"))
async def notes_callback(query: CallbackQuery):
    if not isinstance(query.message, Message):
        return

    data = query.data
    member = await query.message.chat.get_member(query.from_user.id)

    if data == "notes:cancel":
        if member.status in ("creator", "administrator"):
            await query.message.edit_text("✅ Cancelled. All notes are safe!")
        else:
            await query.answer("You don't have permission to do this.", show_alert=True)
        return

    if data.startswith("notes:rmall:"):
        if member.status != "creator":
            return await query.answer("Only the group owner can do this!", show_alert=True)
        chat_id = int(data.split(":")[2])
        await sql.rm_all_notes(chat_id)
        await query.message.edit_text("🗑️ All notes have been deleted.")
        await query.answer()


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

__help__ = """
<b>📋 Notes</b>

Save and recall notes in your group. Notes can store text, photos, videos, stickers, documents and more!

<b>Everyone</b>
- /get &lt;notename&gt; — Get a note
- #notename — Shortcut to get a note
- /notes or /saved — List all saved notes in this chat

<b>Admins only</b>
- /save &lt;notename&gt; &lt;text&gt; — Save a text note
- /save &lt;notename&gt; — Reply to any message to save it as a note
- /clear &lt;notename&gt; — Delete a specific note

<b>Owner only</b>
- /removeallnotes — Wipe all notes (asks for confirmation)

<b>💡 Tips</b>
- Add inline buttons: <code>[Label](buttonurl:https://example.com)</code>
- Same-line buttons: add <code>:same</code> → <code>[Btn](buttonurl:url:same)</code>
- Random responses: separate variants with <code>%%%</code>
- Note names are always lowercase
"""

from PglRobot.utils.help_system import register_help
register_help("Notes", __help__)
