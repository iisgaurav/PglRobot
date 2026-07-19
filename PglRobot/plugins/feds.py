# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode, ChatMemberStatus

from PglRobot.utils.admin_filters import IsAdmin
from PglRobot.database import feds_sql as sql
from PglRobot.utils.help_system import register_help

logger = logging.getLogger(__name__)
feds_router = Router()

ADMIN = IsAdmin("can_restrict_members")
CREATOR = IsAdmin("creator")


@feds_router.message(Command("newfed"))
async def new_fed(message: Message, command: CommandObject):
    fed_name = command.args
    if not fed_name:
        return await message.reply("Please provide a name for your federation.")
        
    fed_id = await sql.create_fed(fed_name, message.from_user.id)
    await message.reply(
        f"🌐 <b>Federation Created!</b>\n\n<b>Name:</b> {fed_name}\n<b>Fed ID:</b> <code>{fed_id}</code>\n\nUse <code>/joinfed {fed_id}</code> in your groups to join this federation.",
        parse_mode=ParseMode.MARKDOWN
    )

@feds_router.message(Command("joinfed"), F.chat.type.in_({"group", "supergroup"}), CREATOR)
async def join_fed_cmd(message: Message, command: CommandObject):
    fed_id = command.args
    if not fed_id:
        return await message.reply("Please provide a Fed ID.")
        
    fed = await sql.get_fed(fed_id)
    if not fed:
        return await message.reply("Federation not found.")
        
    await sql.join_fed(message.chat.id, fed_id)
    await message.reply(f"✅ <b>Successfully joined the federation:</b> {fed.fed_name}")

@feds_router.message(Command("leavefed"), F.chat.type.in_({"group", "supergroup"}), CREATOR)
async def leave_fed_cmd(message: Message):
    fed_id = await sql.get_fed_by_chat(message.chat.id)
    if not fed_id:
        return await message.reply("This group is not in any federation.")
        
    await sql.leave_fed(message.chat.id)
    await message.reply("✅ <b>Successfully left the federation.</b>")

@feds_router.message(Command("fban"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def fban_user(message: Message, command: CommandObject, bot: Bot):
    fed_id = await sql.get_fed_by_chat(message.chat.id)
    if not fed_id:
        return await message.reply("This group is not in a federation.")
        
    fed = await sql.get_fed(fed_id)
    if str(message.from_user.id) != str(fed.owner_id):
        return await message.reply("Only the Federation Owner can fban users.")
        
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
            return await message.reply("Please reply to a user or provide their ID.")
            
    if not target_user:
        return await message.reply("Please reply to a user or provide their ID.")
        
    await sql.add_fban(fed_id, target_user.id, message.from_user.id, reason)
    await message.reply(f"🔨 <b>Fed Ban Executed!</b>\n<b>User:</b> {target_user.first_name}\n<b>Fed:</b> {fed.fed_name}", parse_mode=ParseMode.MARKDOWN)

@feds_router.message(Command("unfban"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def unfban_user(message: Message, command: CommandObject, bot: Bot):
    fed_id = await sql.get_fed_by_chat(message.chat.id)
    if not fed_id:
        return await message.reply("This group is not in a federation.")
        
    fed = await sql.get_fed(fed_id)
    if str(message.from_user.id) != str(fed.owner_id):
        return await message.reply("Only the Federation Owner can unfban users.")
        
    args = command.args
    target_user = None
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif args:
        try:
            target_user_id = int(args.split()[0])
            target_user = await bot.get_chat(target_user_id)
        except ValueError:
            return await message.reply("Please reply to a user or provide their ID.")
            
    if not target_user:
        return await message.reply("Please reply to a user or provide their ID.")
        
    await sql.remove_fban(fed_id, target_user.id)
    await message.reply(f"✅ <b>Fed Ban Removed!</b>\n<b>User:</b> {target_user.first_name}", parse_mode=ParseMode.MARKDOWN)

# Passive FBan Enforcement when they join
@feds_router.chat_member()
async def fban_enforcer_join(event: ChatMemberUpdated, bot: Bot):
    if event.new_chat_member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED):
        fed_id = await sql.get_fed_by_chat(event.chat.id)
        if not fed_id:
            return
            
        is_banned = await sql.is_fbanned(fed_id, event.new_chat_member.user.id)
        if is_banned:
            try:
                await bot.ban_chat_member(event.chat.id, event.new_chat_member.user.id)
                logger.info(f"FBanned user {event.new_chat_member.user.id} was banned upon joining {event.chat.id}")
            except Exception:
                pass


__help__ = """
<b>🤝 Federations (Feds)</b>

Federations allow you to share a global ban list across multiple groups! If a user is FBanned, they are banned from all groups in the federation.

<b>Commands:</b>
• /newfed <code><name></code> — Create a new federation.
• /joinfed <code><fed_id></code> — (Group Creator only) Join your group to a fed.
• /leavefed — (Group Creator only) Leave the current fed.
• /fban <code><reply/id></code> — (Fed Owner only) Ban a user from the entire federation.
• /unfban <code><reply/id></code> — (Fed Owner only) Unban a user from the federation.
"""

register_help("Federations", __help__)
