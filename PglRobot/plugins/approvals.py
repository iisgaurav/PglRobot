# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: @VegaCodesHQ (vegacodes.com)
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from PglRobot.database import approve_sql
from PglRobot.plugins.admin import is_admin

approvals_router = Router()

@approvals_router.message(Command("approve"))
async def approve_user(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups, not in PM!")
    
    if not await is_admin(message, message.from_user.id):
        return await message.reply("You need to be an admin to do this.")
    
    target_user_id = None
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    elif len(message.text.split()) > 1:
        try:
            target_user_id = int(message.text.split()[1])
        except ValueError:
            return await message.reply("Please specify a valid user ID or reply to their message.")
            
    if not target_user_id:
        return await message.reply("Reply to a user's message or specify their user ID to approve them.")
        
    await approve_sql.approve(chat_id, target_user_id)
    await message.reply(f"User <code>{target_user_id}</code> has been approved in this group! They will now bypass locks and blacklists.")


@approvals_router.message(Command("disapprove"))
async def disapprove_user(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups, not in PM!")
    
    if not await is_admin(message, message.from_user.id):
        return await message.reply("You need to be an admin to do this.")
    
    target_user_id = None
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    elif len(message.text.split()) > 1:
        try:
            target_user_id = int(message.text.split()[1])
        except ValueError:
            return await message.reply("Please specify a valid user ID or reply to their message.")
            
    if not target_user_id:
        return await message.reply("Reply to a user's message or specify their user ID to disapprove them.")
        
    removed = await approve_sql.disapprove(chat_id, target_user_id)
    if removed:
        await message.reply(f"User <code>{target_user_id}</code> is no longer approved in this group.")
    else:
        await message.reply(f"User <code>{target_user_id}</code> was not approved anyway.")


@approvals_router.message(Command("approved"))
async def list_approved(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups, not in PM!")
        
    if not await is_admin(message, message.from_user.id):
        return await message.reply("You need to be an admin to do this.")
        
    approved_users = await approve_sql.list_approved(chat_id)
    if not approved_users:
        return await message.reply("No users are currently approved in this group.")
        
    text = "<b>Approved Users:</b>\n"
    for user_id in approved_users:
        text += f"- <code>{user_id}</code>\n"
        
    await message.reply(text)


__help__ = """
<b>Admin Commands:</b>
- /approve [user]: Whitelists a user in the group.
- /disapprove [user]: Removes whitelist.
- /approved: Lists all approved users.
"""

from PglRobot.utils.help_system import register_help
register_help("Approvals", __help__)
