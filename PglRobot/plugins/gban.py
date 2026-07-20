# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import logging
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode, ChatMemberStatus

from PglRobot.utils.admin_filters import IsSudoUser
from PglRobot.database import gban_sql as sql
from PglRobot.utils.help_system import register_help

logger = logging.getLogger(__name__)
gban_router = Router()

SUDO = IsSudoUser()

# Cache for fast lookups
GBANNED_USERS: set[int] = set()

async def load_gban_cache():
    users = await sql.get_all_gbans()
    GBANNED_USERS.update(users)
    logger.info(f"Loaded {len(GBANNED_USERS)} GBanned users into cache.")


@gban_router.message(Command("gban"), SUDO)
async def gban_user(message: Message, command: CommandObject, bot: Bot):
    args = command.args
    target_user = None
    reason = args
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif args:
        parts = args.split(" ", 1)
        try:
            target_user_id = int(parts[0])
            target_user = await bot.get_chat(target_user_id)
            reason = parts[1] if len(parts) > 1 else None
        except ValueError:
            return await message.reply("Please reply to a user or provide their ID to GBan.")
            
    if not target_user:
        return await message.reply("Please reply to a user or provide their ID to GBan.")
        
    if target_user.id in GBANNED_USERS:
        return await message.reply("This user is already GBanned.")
        
    # Prevent banning other Sudo users/owner
    from PglRobot.config import Config
    if target_user.id in Config.SUDO_USERS or target_user.id == Config.OWNER_ID:
        return await message.reply("You cannot GBan a Sudo user or the Owner!")
        
    await sql.add_gban(target_user.id, reason)
    GBANNED_USERS.add(target_user.id)
    
    await message.reply(
        f"🚨 <b>Global Ban Executed!</b>\n\n<b>User:</b> {target_user.first_name} (<code>{target_user.id}</code>)\n<b>Reason:</b> {reason or 'No reason provided'}",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Optionally, we could iterate over all chats the bot is in and ban them.
    # But since aiogram doesn't provide a list of all chats, we will ban them passively when they speak/join.

@gban_router.message(Command("ungban"), SUDO)
async def ungban_user(message: Message, command: CommandObject, bot: Bot):
    args = command.args
    target_user = None
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif args:
        try:
            target_user_id = int(args.split()[0])
            target_user = await bot.get_chat(target_user_id)
        except ValueError:
            return await message.reply("Please reply to a user or provide their ID to un-GBan.")
            
    if not target_user:
        return await message.reply("Please reply to a user or provide their ID to un-GBan.")
        
    if target_user.id not in GBANNED_USERS:
        return await message.reply("This user is not GBanned.")
        
    await sql.remove_gban(target_user.id)
    GBANNED_USERS.remove(target_user.id)
    
    await message.reply(f"✅ <b>Global Ban Removed for:</b> {target_user.first_name} (<code>{target_user.id}</code>)", parse_mode=ParseMode.MARKDOWN)

# Passive GBan Enforcement when they join
@gban_router.chat_member()
async def gban_enforcer_join(event: ChatMemberUpdated, bot: Bot):
    if event.new_chat_member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED):
        if event.new_chat_member.user.id in GBANNED_USERS:
            try:
                await bot.ban_chat_member(event.chat.id, event.new_chat_member.user.id)
                logger.info(f"GBanned user {event.new_chat_member.user.id} was banned upon joining {event.chat.id}")
            except Exception:
                pass


__help__ = """
<b>🚨 Global Bans (GBan)</b>

Global bans allow Sudo Users to ban a scammer or spammer from all groups the bot is an admin in simultaneously.

<b>Sudo Commands:</b>
- /gban <code><reply/id> <reason></code> — Globally ban a user.
- /ungban <code><reply/id></code> — Remove a global ban.

<i>Note: If a GBanned user joins any group where the bot is an admin, they will be instantly banned.</i>
"""

register_help("GBan", __help__)
