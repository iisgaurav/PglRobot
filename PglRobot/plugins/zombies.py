# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: @VegaCodesHQ (vegacodes.com)
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import logging
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode

from PglRobot.utils.admin_filters import IsAdmin
from PglRobot.utils.help_system import register_help
from PglRobot.telethon_client import tbot
from telethon import errors

logger = logging.getLogger(__name__)
zombies_router = Router()

ADMIN = IsAdmin("can_restrict_members")


@zombies_router.message(Command("zombies"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def zombies_handler(message: Message, bot: Bot, command: CommandObject):
    chat_id = message.chat.id
    args = command.args.lower() if command.args else ""
    is_clean = args == "clean"
    
    status_msg = await message.reply("🧟‍♂️ <b>Scanning for zombies (deleted accounts)...</b>\n<i>This might take a minute in large groups.</i>", parse_mode=ParseMode.HTML)
    
    deleted_accounts = []
    
    try:
        # Use Telethon to get all members
        async for user in tbot.iter_participants(chat_id):
            if user.deleted:
                deleted_accounts.append(user.id)
                
    except errors.ChatAdminRequiredError:
        return await status_msg.edit_text("❌ <b>Error:</b> I need to be an admin to scan for zombies.", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Telethon iter_participants error: {e}")
        return await status_msg.edit_text(f"❌ <b>Error occurred during scan:</b> {e}", parse_mode=ParseMode.HTML)
        
    if not deleted_accounts:
        return await status_msg.edit_text("✅ <b>Group is clean!</b> No deleted accounts found.", parse_mode=ParseMode.HTML)
        
    if not is_clean:
        return await status_msg.edit_text(
            f"🧟‍♂️ <b>Found {len(deleted_accounts)} deleted accounts!</b>\n\nTo remove them, use: <code>/zombies clean</code>",
            parse_mode=ParseMode.HTML
        )
        
    await status_msg.edit_text(f"🧹 <b>Removing {len(deleted_accounts)} deleted accounts...</b>", parse_mode=ParseMode.HTML)
    
    kicked = 0
    failed = 0
    
    for uid in deleted_accounts:
        try:
            # We use Aiogram to ban since we are in the Aiogram handler flow (and to trigger our local logging)
            # Alternatively we could use tbot.kick_participant
            await bot.ban_chat_member(chat_id, uid)
            await bot.unban_chat_member(chat_id, uid) # unban so they aren't permanently blacklisted (kicking them)
            kicked += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.3) # Avoid flood limits
        
    await status_msg.edit_text(
        f"✅ <b>Cleanup Complete!</b>\n\n🧹 Kicked: <code>{kicked}</code>\n❌ Failed: <code>{failed}</code>",
        parse_mode=ParseMode.HTML
    )


__help__ = """
<b>🧟‍♂️ Zombies (Deleted Accounts)</b>

Find and remove "Deleted Accounts" from your group to keep it clean and active!

<b>Admin Commands:</b>
• /zombies — Scan the group and count how many deleted accounts there are.
• /zombies clean — Scan and kick all deleted accounts automatically.
"""

register_help("Zombies", __help__)
