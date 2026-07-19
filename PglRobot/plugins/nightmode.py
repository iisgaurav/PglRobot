# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: @VegaCodesHQ (vegacodes.com)
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode

from PglRobot.utils.admin_filters import IsAdmin
from PglRobot.database import nightmode_sql as sql
from PglRobot.utils.help_system import register_help
import asyncio

logger = logging.getLogger(__name__)
nightmode_router = Router()

ADMIN = IsAdmin("can_restrict_members")

# Night mode locks send_messages and media. It allows pins and info change to admins only naturally.
NIGHT_LOCKED_PERMS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_change_info=False,
    can_invite_users=True,
    can_pin_messages=False
)

# Open allows everything back (usually groups have these by default)
NIGHT_UNLOCKED_PERMS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_change_info=False,
    can_invite_users=True,
    can_pin_messages=False
)

@nightmode_router.message(Command("nightmode"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def nightmode_cmd(message: Message, command: CommandObject):
    args = command.args.lower() if command.args else ""
    chat_id = message.chat.id
    
    if args in ("on", "yes", "true", "enable"):
        if await sql.is_nightmode_enabled(chat_id):
            return await message.reply("Night Mode is already enabled in this chat.")
            
        await sql.set_nightmode(chat_id, True)
        await message.reply(
            f"✅ <b>Night Mode Enabled!</b>\n\nThis group will now automatically lock at <b>12:00 AM (IST)</b> and unlock at <b>6:00 AM (IST)</b>.",
            parse_mode=ParseMode.MARKDOWN
        )
    elif args in ("off", "no", "false", "disable"):
        if not await sql.is_nightmode_enabled(chat_id):
            return await message.reply("Night Mode is already disabled in this chat.")
            
        await sql.set_nightmode(chat_id, False)
        await message.reply("❌ <b>Night Mode Disabled!</b>", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("Usage: <code>/nightmode on</code> or <code>/nightmode off</code>", parse_mode=ParseMode.MARKDOWN)


async def job_lock(bot: Bot):
    chats = await sql.get_all_nightmode_chats()
    for chat_id in chats:
        try:
            await bot.set_chat_permissions(chat_id, NIGHT_LOCKED_PERMS)
            await bot.send_message(
                chat_id,
                "🌙 <b>Night Mode Started!</b>\n\n<i>Group is now locked until 6:00 AM (IST). Sleep well!</i>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to lock chat {chat_id} for nightmode: {e}")
        await asyncio.sleep(0.5)

async def job_unlock(bot: Bot):
    chats = await sql.get_all_nightmode_chats()
    for chat_id in chats:
        try:
            await bot.set_chat_permissions(chat_id, NIGHT_UNLOCKED_PERMS)
            await bot.send_message(
                chat_id,
                "☀️ <b>Good Morning!</b>\n\n<i>Night Mode ended. Group is now unlocked.</i>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to unlock chat {chat_id} for nightmode: {e}")
        await asyncio.sleep(0.5)

def setup_nightmode(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
    
    # Lock at 11:55 PM (23:55) IST
    scheduler.add_job(job_lock, trigger="cron", hour=23, minute=55, args=[bot])
    
    # Unlock at 6:00 AM (06:00) IST
    scheduler.add_job(job_unlock, trigger="cron", hour=6, minute=0, args=[bot])
    
    scheduler.start()
    logger.info("Night Mode scheduler started.")


__help__ = """
<b>🌙 Night Mode</b>

Night mode automatically locks the group chat at night so members can't spam while admins are asleep! 

When enabled, the group will automatically close at <b>12:00 AM (IST)</b> and open at <b>6:00 AM (IST)</b>.

<b>Admin Commands:</b>
• /nightmode <code><on/off></code> — Enable or disable night mode in your group.
"""

register_help("Night Mode", __help__)
