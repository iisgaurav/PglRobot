# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from PglRobot.database import trust_sql
from PglRobot.plugins.admin import is_admin

trust_router = Router()

@trust_router.message(Command("trust"))
async def add_trust(message: Message):
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
        return await message.reply("Reply to a user's message or specify their user ID to increase their trust score.")
        
    score = await trust_sql.add_trust(chat_id, target_user_id)
    await message.reply(f"User <code>{target_user_id}</code> has gained +1 Trust! Current score: <b>{score}</b>")


@trust_router.message(Command("untrust"))
async def remove_trust(message: Message):
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
        return await message.reply("Reply to a user's message or specify their user ID to decrease their trust score.")
        
    score = await trust_sql.remove_trust(chat_id, target_user_id)
    await message.reply(f"User <code>{target_user_id}</code> has lost -1 Trust. Current score: <b>{score}</b>")


@trust_router.message(Command("trustscore"))
async def check_trust(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups, not in PM!")
    
    target_user_id = message.from_user.id
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
        
    score = await trust_sql.get_trust(chat_id, target_user_id)
    await message.reply(f"User <code>{target_user_id}</code> has a trust score of: <b>{score}</b>")


__help__ = """
<b>Admin Commands:</b>
- /trust [user]: Adds 1 trust score to the user.
- /untrust [user]: Removes 1 trust score from the user.

<b>User Commands:</b>
- /trustscore [user]: Shows trust score.
"""

from PglRobot.utils.help_system import register_help
register_help("Trust", __help__)
