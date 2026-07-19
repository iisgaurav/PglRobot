# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: AuraX Network
# Powered By: VegaCodesHQ (vegacodes.com)
# Lead Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router, Bot, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery
)
from aiogram.enums import ParseMode

from PglRobot.config import Config
from PglRobot.database.users_sql import update_user

router = Router()

# Path to the banner image shipped with the bot
BANNER_URL = "https://telegra.ph/file/f1d7b30b05ba9f0dbf4e5.jpg"

# ---------------------------------------------------------------------------
# Keyboards
# ---------------------------------------------------------------------------

def start_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Add Me to a Group",
                url=f"https://t.me/{bot_username}?startgroup=true"
            ),
        ],
        [
            InlineKeyboardButton(text="📖 Help", callback_data="start:help"),
            InlineKeyboardButton(text="ℹ️ About", callback_data="start:about"),
        ],
        [
            InlineKeyboardButton(text="💬 Support", url="https://t.me/AuraXSupport"),
            InlineKeyboardButton(text="📢 Updates", url="https://t.me/TeamAuraX/4"),
        ],
        [
            InlineKeyboardButton(
                text="👨‍💻 Owner",
                url=f"https://t.me/{Config.OWNER_USERNAME}"
            ),
        ],
    ])

def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back", callback_data="start:back")]
    ])

# ---------------------------------------------------------------------------
# Message Templates
# ---------------------------------------------------------------------------

def get_start_caption(first_name: str) -> str:
    return (
        f"👋 <b>Hey {first_name}!</b>\n\n"
        f"🤖 I'm <b>PglRobot</b> — a next-generation moderation engine </b>.\n"
        f"🏢 <b>Powered by:</b> @TeamAuraX\n\n"
        f"<b>Why choose me?</b>\n"
        f"⚡ <b>Blazing Fast</b>: Powered by an asynchronous hybrid engine (Aiogram 3 + Telethon) for zero-lag moderation.\n"
        f"🛡️ <b>Intelligent Anti-Spam</b>: Instantly detects and bans crypto-scammers and spam rings.\n"
        f"🌐 <b>Federations</b>: Connect multiple groups under one global ban network.\n"
        f"👮 <b>Advanced Moderation</b>: Temp-bans, mutes, automated warnings, and dynamic locks.\n\n"
        f"<i>Add me to your group and promote me to admin to instantly secure your chat!</i>"
    )

ABOUT_TEXT = (
    "🤖 <b>About PglRobot</b>\n\n"
    "<b>Version:</b> <code>2.0</code>\n"
    "<b>Ecosystem:</b> <code>@TeamAuraX</code>\n"
    "<b>Framework:</b> <code>Aiogram 3.x + Telethon</code>\n"
    "<b>Language:</b> <code>Python 3.11+</code>\n"
    "<b>Database:</b> <code>PostgreSQL (asyncpg)</code>\n"
    "<b>Strict Typing:</b> <code>100% basedpyright</code>\n\n"
    "An official @VegaCodesHQ Initiative.\n"
    "Built from scratch with ❤️ by @{owner}.\n\n"
    "<i>Blazing fast, 100% async, crash-proof, and built to handle massive communities.</i>"
)

# ---------------------------------------------------------------------------
# /start — Private Chat
# ---------------------------------------------------------------------------

@router.message(CommandStart(), F.chat.type == "private")
async def start_private(message: Message, bot: Bot, command: CommandObject):
    user = message.from_user

    await update_user(user.id, user.username, message.chat.id, None)

    # Deep-link payloads are handled by help.py
    if command.args:
        return

    me = await bot.get_me()
    bot_username = me.username or ""
    caption = get_start_caption(user.first_name or "there")

    # Send banner photo with caption via Telegraph URL for instant caching
    try:
        await message.answer_photo(
            photo=BANNER_URL,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=start_keyboard(bot_username),
        )
    except Exception:
        # Fallback to text if URL fails
        await message.answer(
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=start_keyboard(bot_username),
        )


# ---------------------------------------------------------------------------
# /start — Group Chat
# ---------------------------------------------------------------------------

@router.message(CommandStart(), F.chat.type.in_({"group", "supergroup"}))
async def start_group(message: Message):
    user = message.from_user
    chat = message.chat

    await update_user(user.id, user.username, chat.id, chat.title)

    await message.answer(
        f"👋 Hey! I'm <b>PglRobot</b>, a next-generation moderation bot built for speed and security.\n\n<i>Admins: use /help to see all available commands.</i>",
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------------------------
# Inline Button Callbacks
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "start:help")
async def cb_help(query: CallbackQuery):
    from PglRobot.utils.help_system import get_all_modules
    modules = get_all_modules()
    lines = "\n".join(f"  • <b>{m}</b>" for m in modules)
    text = (
        "📖 <b>Available Modules:</b>\n\n"
        f"{lines}\n\n"
        "<i>Send /help in PM to browse them interactively with buttons!</i>"
    )
    if not isinstance(query.message, Message):
        return
    await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
    await query.answer()


@router.callback_query(F.data == "start:about")
async def cb_about(query: CallbackQuery):
    text = ABOUT_TEXT.format(owner=Config.OWNER_USERNAME)
    if not isinstance(query.message, Message):
        return
    await query.message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=back_keyboard())
    await query.answer()


@router.callback_query(F.data == "start:back")
async def cb_back(query: CallbackQuery, bot: Bot):
    me = await bot.get_me()
    caption = get_start_caption(query.from_user.first_name or "there")
    if not isinstance(query.message, Message):
        return
    await query.message.edit_caption(
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=start_keyboard(me.username if me.username else "bot"),
    )
    await query.answer()
