# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import asyncio
import logging
import time

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

from PglRobot.utils.admin_filters import IsAdmin

logger = logging.getLogger(__name__)
purge_router = Router()

ADMIN = IsAdmin("can_delete_messages")

# ---------------------------------------------------------------------------
# /purge — delete from replied message up to here  [ADMIN FIRST]
# Usage: /purge        → delete from reply to here
#        /purge <N>    → delete N messages from reply
# ---------------------------------------------------------------------------

@purge_router.message(
    Command("purge", prefix="/!"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN,
)
async def purge_messages(message: Message, bot: Bot, command: CommandObject | None = None):
    if not message.reply_to_message:
        return await message.reply(
            "Reply to a message to mark where the purge starts.\nUsage: <code>/purge</code> or <code>/purge 50</code>",
            parse_mode=ParseMode.HTML,
        )

    start_time = time.perf_counter()
    start_id = message.reply_to_message.message_id
    end_id = message.message_id

    args = command.args if command else None
    if not args and message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            args = parts[1]

    if args and args.strip().isdigit():
        count = min(int(args.strip()), 1000)
        ids_to_delete = list(range(start_id, start_id + count + 1)) + [end_id]
    else:
        ids_to_delete = list(range(start_id, end_id + 1))

    # CAP HUGE PURGES to avoid DoS
    if len(ids_to_delete) > 2000:
        ids_to_delete = ids_to_delete[:2000]

    ids_to_delete = sorted(set(ids_to_delete))

    status_msg = None
    if len(ids_to_delete) > 50:
        status_msg = await message.answer(
            f"🗑️ Purging <code>{len(ids_to_delete)}</code> messages...",
            parse_mode=ParseMode.HTML,
        )

    deleted = await _delete_messages_in_chunks(bot, message.chat.id, ids_to_delete)
    elapsed = time.perf_counter() - start_time

    result = f"✅ Purged <b>{deleted}</b> messages in <code>{elapsed:.2f}s</code>"
    if deleted == 0:
        result = "❌ Failed to purge any messages. Please check if I have <b>Delete Messages</b> permission in this group!"

    try:
        if status_msg:
            await status_msg.edit_text(result, parse_mode=ParseMode.HTML)
            await asyncio.sleep(4)
            await status_msg.delete()
        else:
            notify = await message.answer(result, parse_mode=ParseMode.HTML)
            await asyncio.sleep(4)
            await notify.delete()
    except TelegramBadRequest:
        pass

# Helpers
# ---------------------------------------------------------------------------

async def _delete_messages_in_chunks(bot: Bot, chat_id: int, message_ids: list[int]) -> int:
    """Delete a list of message IDs in chunks of 100. Returns count deleted."""
    deleted = 0
    for i in range(0, len(message_ids), 100):
        chunk = message_ids[i : i + 100]
        try:
            await bot.delete_messages(chat_id, chunk)
            deleted += len(chunk)
        except TelegramBadRequest as e:
            logger.warning("Chunk delete failed due to Bad Request: %s", e)
        except Exception as e:
            logger.warning("Chunk delete error: %s", e)
            logger.warning("Chunk delete error: %s", e)
    return deleted


# ---------------------------------------------------------------------------
# PM fallback
# ---------------------------------------------------------------------------

@purge_router.message(
    Command("purge", "purgefrom", "del", "purgeall"),
    F.chat.type == "private",
)
async def purge_pm(message: Message):
    await message.reply("This command can only be used in groups.")


# ---------------------------------------------------------------------------
# /del — delete the replied-to message + the command itself  [ADMIN FIRST]
# ---------------------------------------------------------------------------

@purge_router.message(
    Command("del"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN,
)
async def del_message(message: Message, bot: Bot):
    if not message.reply_to_message:
        return await message.reply("Reply to a message to delete it.")

    try:
        await bot.delete_messages(
            message.chat.id,
            [message.reply_to_message.message_id, message.message_id]
        )
    except TelegramBadRequest as e:
        await message.reply(f"❌ Couldn't delete: {e.message}")


# /del fallback — not admin
@purge_router.message(
    Command("del"),
    F.chat.type.in_({"group", "supergroup"}),
)
async def del_not_admin(message: Message):
    await message.reply(
        "❌ You need to be an admin with <b>Delete Messages</b> permission.",
        parse_mode=ParseMode.HTML
    )


# ---------------------------------------------------------------------------
# /purge — delete from replied message up to here  [ADMIN FIRST]
# Usage: /purge        → delete from reply to here
#        /purge <N>    → delete N messages from reply
# ---------------------------------------------------------------------------

@purge_router.message(
    Command("purge", prefix="/!"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN,
)
async def purge_messages(message: Message, bot: Bot, command: CommandObject | None = None):
    logger.error("DEBUG: purge_messages STARTED")
    if not message.reply_to_message:
        logger.error("DEBUG: No reply_to_message")
        return await message.reply(
            "Reply to a message to mark where the purge starts.\nUsage: <code>/purge</code> or <code>/purge 50</code>",
            parse_mode=ParseMode.HTML,
        )

    start_time = time.perf_counter()
    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    logger.error(f"DEBUG: start_id={start_id}, end_id={end_id}")

    args = command.args if command else None
    if not args and message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            args = parts[1]

    if args and args.strip().isdigit():
        count = min(int(args.strip()), 1000)
        ids_to_delete = list(range(start_id, start_id + count + 1)) + [end_id]
        logger.error(f"DEBUG: Generated count ids: len={len(ids_to_delete)}")
    else:
        ids_to_delete = list(range(start_id, end_id + 1))
        logger.error(f"DEBUG: Generated range ids: len={len(ids_to_delete)}")

    # CAP HUGE PURGES to avoid DoS
    if len(ids_to_delete) > 2000:
        logger.error("DEBUG: Cap triggered. Setting ids_to_delete to 2000")
        ids_to_delete = ids_to_delete[:2000]

    ids_to_delete = sorted(set(ids_to_delete))

    status_msg = None
    if len(ids_to_delete) > 50:
        logger.error("DEBUG: Sending status_msg")
        status_msg = await message.answer(
            f"🗑️ Purging <code>{len(ids_to_delete)}</code> messages...",
            parse_mode=ParseMode.HTML,
        )

    logger.error("DEBUG: Calling _delete_messages_in_chunks")
    deleted = await _delete_messages_in_chunks(bot, message.chat.id, ids_to_delete)
    elapsed = time.perf_counter() - start_time
    logger.error(f"DEBUG: _delete_messages_in_chunks returned {deleted} in {elapsed}s")

    result = f"✅ Purged <b>{deleted}</b> messages in <code>{elapsed:.2f}s</code>"
    if deleted == 0:
        result = "❌ Failed to purge any messages. Please check if I have <b>Delete Messages</b> permission in this group!"

    try:
        if status_msg:
            await status_msg.edit_text(result, parse_mode=ParseMode.HTML)
            await asyncio.sleep(4)
            await status_msg.delete()
        else:
            notify = await message.answer(result, parse_mode=ParseMode.HTML)
            await asyncio.sleep(4)
            await notify.delete()
    except TelegramBadRequest:
        pass


# /purge fallback — not admin
@purge_router.message(
    Command("purge", prefix="/!"),
    F.chat.type.in_({"group", "supergroup"}),
)
async def purge_not_admin(message: Message):
    await message.reply(
        "❌ You need to be an admin with <b>Delete Messages</b> permission.",
        parse_mode=ParseMode.HTML
    )


# ---------------------------------------------------------------------------
# /purgefrom <message_id>  [ADMIN FIRST]
# ---------------------------------------------------------------------------

@purge_router.message(
    Command("purgefrom"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN,
)
async def purge_from(message: Message, bot: Bot, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        return await message.reply(
            "Usage: /purgefrom <code>&lt;message_id&gt;</code>\nPurges from that message ID up to this message.",
            parse_mode=ParseMode.HTML,
        )

    start_id = int(command.args.strip())
    end_id = message.message_id

    if start_id >= end_id:
        return await message.reply("❌ Start message ID must be less than current message ID.")

    ids = list(range(start_id, end_id + 1))
    if len(ids) > 5000:
        return await message.reply("❌ Cannot purge more than 5000 messages at once.")

    deleted = await _delete_messages_in_chunks(bot, message.chat.id, ids)
    try:
        notify = await message.answer(
            f"✅ Purged <b>{deleted}</b> messages from ID <code>{start_id}</code>.",
            parse_mode=ParseMode.HTML,
        )
        await asyncio.sleep(3)
        await notify.delete()
    except TelegramBadRequest:
        pass


# /purgefrom fallback — not admin
@purge_router.message(
    Command("purgefrom"),
    F.chat.type.in_({"group", "supergroup"}),
)
async def purgefrom_not_admin(message: Message):
    await message.reply(
        "❌ You need to be an admin with <b>Delete Messages</b> permission.",
        parse_mode=ParseMode.HTML
    )


# ---------------------------------------------------------------------------
# /purgeall — owner only
# ---------------------------------------------------------------------------

@purge_router.message(
    Command("purgeall"),
    F.chat.type.in_({"group", "supergroup"}),
)
async def purge_all(message: Message, bot: Bot):
    member = await message.chat.get_member(message.from_user.id)
    if member.status != "creator":
        return await message.reply("⚠️ Only the group owner can use /purgeall!")

    warn = await message.reply(
        "⚠️ <b>WARNING:</b> Deleting all recent messages (last 48h only).\n<i>Proceeding in 5 seconds...</i>",
        parse_mode=ParseMode.HTML,
    )
    await asyncio.sleep(5)

    ids = list(range(max(1, message.message_id - 5000), message.message_id + 1))
    deleted = await _delete_messages_in_chunks(bot, message.chat.id, ids)

    try:
        await warn.edit_text(
            f"✅ Purged approximately <b>{deleted}</b> messages.",
            parse_mode=ParseMode.HTML,
        )
    except TelegramBadRequest:
        pass


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

__help__ = """
<b>🗑️ Purge</b>

<b>Admins only:</b>
• /del — Delete the replied-to message
• /purge — Delete all messages from the replied message to here
• /purge &lt;N&gt; — Delete N messages starting from the replied message
• /purgefrom &lt;message_id&gt; — Purge from a specific message ID

<b>Owner only:</b>
• /purgeall — Delete all recent messages (last 48 hours)

<b>Note:</b> Telegram only allows deleting messages newer than 48 hours.
"""

from PglRobot.utils.help_system import register_help
register_help("Purge", __help__)
