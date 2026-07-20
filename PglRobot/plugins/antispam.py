# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import re
import logging
from aiogram import Router, F, Bot
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus

from PglRobot.utils.admin_filters import IsAdmin, BotCan

logger = logging.getLogger(__name__)
antispam_router = Router()

# --- In-memory toggle store (per chat) ---
# Key: chat_id, Value: True (enabled) / False (disabled)
_antispam_enabled: dict[int, bool] = {}

def is_antispam_on(chat_id: int) -> bool:
    return _antispam_enabled.get(chat_id, False)  # OFF by default — admin must explicitly enable

# ---------------------------------------------------------------------------
# Spam Detection Patterns
# ---------------------------------------------------------------------------

SPAM_KEYWORDS = [
    # Crypto/USDT exchange
    r"\busdt\b", r"\binr\b", r"1usdt\s*=", r"usdt.*inr", r"inr.*usdt",
    r"exchange.*usdt", r"usdt.*exchange",
    # Fund types used by scammers
    r"\bgame\s*fund\b", r"\bstock\s*fund\b", r"\bmixed\s*fund\b",
    r"\bhacker\s*fund\b", r"\bhazardous\s*fund\b", r"\bfraudulent\s*fund\b",
    r"\bthief.*fund\b", r"\bsteal\s*fund\b",
    # Common spam phrases
    r"prepayment\s*required",
    r"we\s*will\s*start\s*working\s*after\s*receiving\s*the\s*deposit",
    r"long.term\s*(partners|cooperation)",
    r"safe.*stable.*efficient",
    r"no\s*p2p",
    r"imps.*upi.*bank\s*card",
    r"wire\s*transfer.*usa",
    r"cashier\s*check",
    r"advance\s*payment.*usdt",
    # Common scam platform mentions
    r"@\w+\s+(boss|person\s*in\s*charge)",
    r"whatsapp.*\+\d{5,}",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SPAM_KEYWORDS]

# How many patterns must match to consider it spam
SPAM_THRESHOLD = 2


def calculate_spam_score(text: str) -> int:
    """Returns number of spam patterns matched in the text."""
    score = 0
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            score += 1
    return score


# ---------------------------------------------------------------------------
# Admin commands
# ---------------------------------------------------------------------------

ADMIN_OR_OWNER = IsAdmin("can_restrict_members")
BOT_CAN_RESTRICT = BotCan("can_restrict_members")


@antispam_router.message(
    Command("antispam"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
)
async def toggle_antispam(message: Message):
    """Toggle anti-spam on/off for this group."""
    chat_id = message.chat.id
    args = message.text.split()

    if len(args) < 2:
        status = "✅ ON" if is_antispam_on(chat_id) else "❌ OFF"
        return await message.reply(
            f"<b>Anti-Spam Status:</b> {status}\n\n" +
            f"Use <code>/antispam on</code> to enable auto-ban of crypto/USDT spammers.\n" +
            f"Use <code>/antispam off</code> to disable it.\n\n" +
            f"<i>⚠️ Disabled by default — must be turned on by an admin.</i>"
        )

    action = args[1].lower()
    if action == "on":
        _antispam_enabled[chat_id] = True
        await message.reply("✅ <b>Anti-Spam enabled!</b> I'll automatically ban crypto/USDT spammers.")
    elif action == "off":
        _antispam_enabled[chat_id] = False
        await message.reply("❌ <b>Anti-Spam disabled.</b> Spam messages will no longer be auto-deleted.")
    else:
        await message.reply("Usage: <code>/antispam on</code> or <code>/antispam off</code>")


@antispam_router.message(
    Command("antispam"),
    F.chat.type == "private",
)
async def antispam_pm(message: Message):
    await message.reply("This command can only be used in groups.")


# ---------------------------------------------------------------------------
# Auto-spam detection middleware handler
# ---------------------------------------------------------------------------

@antispam_router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def auto_antispam(message: Message, bot: Bot):
    """Automatically detect and remove spam messages."""
    if not message.from_user:
        return

    chat_id = message.chat.id

    # Check if anti-spam is enabled for this group
    if not is_antispam_on(chat_id):
        raise SkipHandler()

    # Skip admins and the bot itself
    try:
        member = await message.chat.get_member(message.from_user.id)
        if member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        ):
            raise SkipHandler()
    except Exception:
        raise SkipHandler()

    text = message.text or ""
    score = calculate_spam_score(text)

    if score >= SPAM_THRESHOLD:
        user = message.from_user
        user_link = f'<a href="tg://user?id={user.id}">{user.full_name}</a>'

        logger.warning(
            f"Spam detected (score={score}) from user {user.id} " +
            f"({user.username}) in chat {chat_id}"
        )

        try:
            # Delete the spam message
            await message.delete()
        except Exception as e:
            logger.error(f"Failed to delete spam message: {e}")

        try:
            # Ban the spammer
            await bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
            await bot.send_message(
                chat_id=chat_id,
                text=(
                    f"🚫 <b>Spammer banned!</b>\n"
                    f"User {user_link} was automatically banned for sending spam.\n"
                    f"<i>(Spam score: {score}/{len(COMPILED_PATTERNS)})</i>"
                ),
            )
            logger.info(f"Banned spammer {user.id} from chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to ban spammer {user.id}: {e}")

    # ALWAYS let the message pass to other handlers (like notes, purge, etc)
    # even if it was spam (it got deleted anyway) or wasn't spam.
    raise SkipHandler()


# ---------------------------------------------------------------------------
# Help string
# ---------------------------------------------------------------------------

__help__ = """
<b>🛡️ Anti-Spam</b>

Automatically detects and bans crypto/USDT exchange spammers.

<b>Commands:</b>
• /antispam — Show current anti-spam status
• /antispam on — Enable auto-spam detection (default: ON)
• /antispam off — Disable auto-spam detection

<b>How it works:</b>
When a non-admin posts a message matching known spam patterns (crypto rates, USDT exchanges, fund types), the bot will:
1. Instantly delete the message
2. Permanently ban the sender
"""

from PglRobot.utils.help_system import register_help
register_help("Anti-Spam", __help__)
