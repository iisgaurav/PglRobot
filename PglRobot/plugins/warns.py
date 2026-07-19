# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: @VegaCodesHQ (vegacodes.com)
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from PglRobot.utils.admin_filters import IsAdmin, BotCan
from PglRobot.utils.extraction import extract_user_and_reason
from PglRobot.database import warns_sql as sql

warns_router = Router()

ADMIN_OR_OWNER = IsAdmin("can_restrict_members")
BOT_CAN_RESTRICT = BotCan("can_restrict_members")

@warns_router.message(Command("warn", "unwarn", "rmwarn", "warns", "warnlimit"), F.chat.type == "private")
async def pm_fallback(message: Message):
    await message.reply("This command can only be used in groups.")


@warns_router.message(Command("warn"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER, BOT_CAN_RESTRICT)
async def warn_user(message: Message, command: CommandObject):
    user_id, reason = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to warn.")
        
    if user_id == message.bot.id:
        return await message.reply("I can't warn myself!")
        
    from PglRobot.utils.admin_filters import check_if_admin
    if await check_if_admin(message.chat, user_id):
        return await message.reply("I'm not going to warn an admin!")
        
    chat_id = message.chat.id
    limit, soft_warn = await sql.get_warn_setting(chat_id)
    
    num_warns, _ = await sql.warn_user(user_id, chat_id, reason)
    
    if num_warns >= limit:
        # Hit limit
        await sql.reset_warns(user_id, chat_id)
        
        if soft_warn:
            # Kick (ban + unban)
            try:
                await message.bot.ban_chat_member(chat_id=message.chat.id, user_id=user_id)
                await message.bot.unban_chat_member(chat_id=message.chat.id, user_id=user_id)
                await message.reply(f"User {user_id} reached {limit} warns and has been kicked.")
            except Exception as e:
                await message.reply(f"User reached warn limit, but I failed to kick them. Error: {str(e)}")
        else:
            # Ban
            try:
                await message.bot.ban_chat_member(chat_id=message.chat.id, user_id=user_id)
                await message.reply(f"User {user_id} reached {limit} warns and has been banned.")
            except Exception as e:
                await message.reply(f"User reached warn limit, but I failed to ban them. Error: {str(e)}")
    else:
        text = f"User {user_id} has been warned. ({num_warns}/{limit})"
        if reason:
            text += f"\nReason: {reason}"
        await message.reply(text)


@warns_router.message(Command("unwarn", "rmwarn"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER)
async def unwarn_user(message: Message, command: CommandObject):
    user_id, _ = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to unwarn.")
        
    removed = await sql.remove_warn(user_id, message.chat.id)
    if removed:
        await message.reply(f"Removed latest warn for user {user_id}.")
    else:
        await message.reply(f"User {user_id} has no warns.")


@warns_router.message(Command("warns"), F.chat.type.in_({"group", "supergroup"}))
async def get_user_warns(message: Message, command: CommandObject):
    user_id, _ = extract_user_and_reason(message, command.args)
    if not user_id:
        # If no user specified, check self
        user_id = message.from_user.id
        
    warns_data = await sql.get_warns(user_id, message.chat.id)
    if not warns_data or warns_data[0] == 0:
        return await message.reply(f"User {user_id} has no warns!")
        
    num, reasons = warns_data
    limit, _ = await sql.get_warn_setting(message.chat.id)
    
    text = f"User {user_id} has {num}/{limit} warns.\n"
    if reasons:
        text += "Reasons:\n"
        for i, reason in enumerate(reasons, 1):
            text += f"{i}. {reason}\n"
            
    await message.reply(text)


@warns_router.message(Command("warnlimit"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER)
async def set_warn_limit(message: Message, command: CommandObject):
    if not command.args:
        limit, _ = await sql.get_warn_setting(message.chat.id)
        return await message.reply(f"Current warn limit is {limit}.")
        
    try:
        new_limit = int(command.args.split()[0])
        if new_limit < 1:
            return await message.reply("Warn limit must be at least 1.")
            
        await sql.set_warn_limit(message.chat.id, new_limit)
        await message.reply(f"Warn limit updated to {new_limit}.")
    except ValueError:
        await message.reply("Please provide a valid number.")

__help__ = """
*Warns Commands:*
 • <code>/warn <user></code>: Warns a user.
 • <code>/unwarn <user></code> or <code>/rmwarn <user></code>: Removes the latest warn from a user.
 • <code>/warns <user></code>: Shows a user's warns.
 • <code>/warnlimit <limit></code>: Sets the warn limit for the chat (default is 3).
"""
from PglRobot.utils.help_system import register_help
register_help("Warns", __help__)
