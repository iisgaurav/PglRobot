# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import logging
from aiogram import Router, F, Bot
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode

from PglRobot.utils.admin_filters import IsAdmin
from PglRobot.database import karma_sql as sql
from PglRobot.utils.help_system import register_help

logger = logging.getLogger(__name__)
karma_router = Router()

ADMIN = IsAdmin("can_change_info")

POSITIVE_TRIGGERS = {"+", "+1", "++", "upvote", "thanks", "thx", "tq", "thank you", "pro", "legend", "hero", "great"}
NEGATIVE_TRIGGERS = {"-", "-1", "--", "downvote", "noob", "idiot", "wtf", "shit", "bad", "worst"}

@karma_router.message(Command("karmatoggle"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def karma_toggle(message: Message, command: CommandObject):
    args = command.args.lower() if command.args else ""
    chat_id = message.chat.id
    
    if args in ("on", "yes", "true", "enable"):
        await sql.set_karma_state(chat_id, True)
        await message.reply("✅ <b>Karma System Enabled!</b>\nReply to messages with <code>+1</code> or <code>-1</code> to give/take karma.", parse_mode=ParseMode.MARKDOWN)
    elif args in ("off", "no", "false", "disable"):
        await sql.set_karma_state(chat_id, False)
        await message.reply("❌ <b>Karma System Disabled!</b>", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("Usage: <code>/karmatoggle on</code> or <code>/karmatoggle off</code>", parse_mode=ParseMode.MARKDOWN)


@karma_router.message(Command("karma"), F.chat.type.in_({"group", "supergroup"}))
async def check_karma(message: Message):
    chat_id = message.chat.id
    if not await sql.is_karma_enabled(chat_id):
        return
        
    target_user = message.from_user
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        
    karma = await sql.get_karma(chat_id, target_user.id)
    await message.reply(f"📈 <b>Karma Stats</b>\nUser: {target_user.first_name}\nKarma: <code>{karma}</code>", parse_mode=ParseMode.MARKDOWN)



@karma_router.message(F.chat.type.in_({"group", "supergroup"}) & F.reply_to_message)
async def karma_handler(message: Message):
    text = message.text or message.caption
    if not text:
        raise SkipHandler()
        
    text = text.lower().strip()
    
    # Simple direct match
    is_positive = text in POSITIVE_TRIGGERS
    is_negative = text in NEGATIVE_TRIGGERS
    
    if not is_positive and not is_negative:
        raise SkipHandler()
        
    chat_id = message.chat.id
    if not await sql.is_karma_enabled(chat_id):
        raise SkipHandler()
        
    giver = message.from_user
    receiver = message.reply_to_message.from_user
    
    if giver.id == receiver.id:
        await message.reply("You can't give karma to yourself!")
        raise SkipHandler()
        
    if receiver.is_bot:
        await message.reply("Bots don't need karma!")
        raise SkipHandler()
        
    if is_positive:
        new_karma = await sql.update_karma(chat_id, receiver.id, 1)
        await message.reply(
            f"✨ <b>Karma Added!</b>\n{receiver.first_name} now has <code>{new_karma}</code> karma.",
            parse_mode=ParseMode.MARKDOWN
        )
    elif is_negative:
        new_karma = await sql.update_karma(chat_id, receiver.id, -1)
        await message.reply(
            f"📉 <b>Karma Deducted!</b>\n{receiver.first_name} now has <code>{new_karma}</code> karma.",
            parse_mode=ParseMode.MARKDOWN
        )


__help__ = """
<b>📈 Karma System</b>

Upvote or downvote users based on their helpfulness!

<b>Admin Commands:</b>
• /karmatoggle <code><on/off></code> — Enable or disable the karma system in your group.

<b>User Commands:</b>
• /karma — Check your karma score. (Or reply to someone to check theirs).
• <code>+1</code>, <code>thanks</code>, <code>pro</code> (reply to a message) — Give 1 karma to a user.
• <code>-1</code>, <code>noob</code>, <code>downvote</code> (reply to a message) — Deduct 1 karma from a user.
"""

register_help("Karma", __help__)
