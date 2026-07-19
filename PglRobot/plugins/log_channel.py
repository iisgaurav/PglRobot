# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import logging
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, Chat
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from PglRobot.utils.admin_filters import IsAdmin
from PglRobot.database import log_channel_sql as sql

logger = logging.getLogger(__name__)
log_router = Router()

ADMIN = IsAdmin("can_change_info")


# ---------------------------------------------------------------------------
# Helpers — used by OTHER plugins to send log messages
# ---------------------------------------------------------------------------

async def send_log(bot: Bot, chat_id: int | str, text: str, parse_mode: str = ParseMode.HTML) -> bool:
    """
    Send a log message to the configured log channel for a group.
    Returns True if sent successfully, False otherwise.
    Called by other plugins (admin, warns, etc.)
    """
    log_channel = await sql.get_log_channel(chat_id)
    if not log_channel:
        return False

    try:
        await bot.send_message(
            chat_id=int(log_channel),
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=True,
        )
        return True
    except TelegramForbiddenError:
        logger.warning("Bot was kicked from log channel %s", log_channel)
        await sql.stop_logging(chat_id)
        return False
    except TelegramBadRequest as e:
        logger.warning("Failed to send log to %s: %s", log_channel, e)
        return False


def log_action(
    action: str,
    chat: Chat,
    by_user_id: int,
    by_user_name: str,
    target_user_id: int | None = None,
    target_user_name: str | None = None,
    reason: str | None = None,
    extra: str | None = None,
) -> str:
    """Build a formatted log message string."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"🔔 <b>#{action.upper()}</b>",
        f"{'━' * 24}",
        f"🏠 <b>Chat:</b> {chat.title} (<code>{chat.id}</code>)",
        f"👮 <b>By:</b> <a href='tg://user?id={by_user_id}'>{by_user_name}</a> (<code>{by_user_id}</code>)",
    ]
    if target_user_id:
        lines.append(
            f"🎯 <b>Target:</b> <a href='tg://user?id={target_user_id}'>{target_user_name}</a> (<code>{target_user_id}</code>)"
        )
    if reason:
        lines.append(f"📝 <b>Reason:</b> {reason}")
    if extra:
        lines.append(f"ℹ️ {extra}")
    lines.append(f"🕐 <b>Time:</b> <code>{now}</code>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PM fallback
# ---------------------------------------------------------------------------

@log_router.message(
    Command("setlog", "unsetlog", "logsettings"),
    F.chat.type == "private",
)
async def log_pm(message: Message):
    await message.reply("This command can only be used in groups.")


# ---------------------------------------------------------------------------
# /setlog — set log channel
# Usage: Forward this command from the group into the target channel,
#        OR use /setlog in the group after forwarding is set up.
# Simpler approach: /setlog <channel_id> in the group
# ---------------------------------------------------------------------------

@log_router.message(
    Command("setlog"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN,
)
async def set_log(message: Message, bot: Bot, command: CommandObject):
    """
    Usage in group: /setlog <channel_id>
    The bot must be an admin in that channel too.
    """
    if not command.args:
        current = await sql.get_log_channel(message.chat.id)
        if current:
            return await message.reply(
                f"📋 Log channel is currently set to <code>{current}</code>.\n" +
                f"Use /unsetlog to remove it.",
                parse_mode=ParseMode.HTML,
            )
        return await message.reply(
            "Usage: <code>/setlog &lt;channel_id&gt;</code>\n\n" +
            "Example: <code>/setlog -1001234567890</code>\n\n" +
            "The bot must be an admin in the target channel.",
            parse_mode=ParseMode.HTML,
        )

    channel_id_str = command.args.strip()
    if not channel_id_str.lstrip("-").isdigit():
        return await message.reply(
            "❌ Invalid channel ID. Use the numeric ID (e.g. <code>-1001234567890</code>).",
            parse_mode=ParseMode.HTML,
        )

    channel_id = int(channel_id_str)

    # Verify bot can post to channel
    try:
        test = await bot.send_message(
            channel_id,
            f"✅ Log channel set for <b>{message.chat.title}</b>!",
            parse_mode=ParseMode.HTML,
        )
        await test.delete()
    except TelegramForbiddenError:
        return await message.reply(
            "❌ I'm not an admin in that channel, or the channel doesn't exist.\n" +
            "Add me as admin with <b>Post Messages</b> permission.",
            parse_mode=ParseMode.HTML,
        )
    except TelegramBadRequest as e:
        return await message.reply(f"❌ Error: <code>{e.message}</code>", parse_mode=ParseMode.HTML)

    await sql.set_log_channel(message.chat.id, channel_id)
    await message.reply(
        f"✅ Log channel set to <code>{channel_id}</code>!\n" +
        f"All moderation actions in this group will now be logged there.",
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------------------------
# /unsetlog — remove log channel
# ---------------------------------------------------------------------------

@log_router.message(
    Command("unsetlog"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN,
)
async def unset_log(message: Message, bot: Bot):
    old = await sql.stop_logging(message.chat.id)
    if not old:
        return await message.reply("❌ No log channel is currently set for this group.")

    try:
        await bot.send_message(
            int(old),
            f"🔕 Log channel unlinked from <b>{message.chat.title}</b>.",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    await message.reply(
        f"✅ Log channel <code>{old}</code> has been unlinked from this group.",
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------------------------
# /logsettings — show current log config
# ---------------------------------------------------------------------------

@log_router.message(
    Command("logsettings"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN,
)
async def log_settings(message: Message):
    current = await sql.get_log_channel(message.chat.id)
    if current:
        text = (
            f"📋 <b>Log Settings for {message.chat.title}</b>\n\n"
            f"✅ <b>Log channel:</b> <code>{current}</code>\n"
            f"<i>All moderation actions are being logged.</i>"
        )
    else:
        text = (
            f"📋 <b>Log Settings for {message.chat.title}</b>\n\n"
            f"❌ <b>No log channel set.</b>\n"
            f"Use /setlog <code>&lt;channel_id&gt;</code> to configure one."
        )
    await message.reply(text, parse_mode=ParseMode.HTML)


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

__help__ = """
<b>📋 Log Channel</b>

Send all moderation events (bans, kicks, warns, mutes) to a private log channel.

<b>Admins only:</b>
• /setlog &lt;channel_id&gt; — Set the log channel (bot must be admin there)
• /unsetlog — Remove the log channel
• /logsettings — View current log configuration

<b>How to set up:</b>
1. Create a private channel
2. Add the bot as admin with Post Messages permission
3. Get the channel ID (use @userinfobot or similar)
4. Run /setlog -100xxxxxxxxxx in your group
"""

from PglRobot.utils.help_system import register_help
register_help("Log Channel", __help__)
