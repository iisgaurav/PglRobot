# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router
import html
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from PglRobot.database import connection_sql

connections_router = Router()

async def resolve_chat(message: Message) -> tuple[int | None, str | None]:
    """
    Helper function for other plugins.
    If run in a group, returns (group_id, group_title).
    If run in PM, returns (connected_chat_id, chat_title) or (None, None).
    """
    if message.chat.type in ["group", "supergroup"]:
        return message.chat.id, message.chat.title
        
    # It's a PM, check for connection
    connected_chat_id = await connection_sql.get_connected_chat(message.from_user.id)
    if connected_chat_id:
        try:
            chat = await message.bot.get_chat(connected_chat_id)
            return chat.id, chat.title
        except TelegramBadRequest:
            return None, None
    return None, None


@connections_router.message(Command("connect"))
async def connect_chat(message: Message):
    if message.chat.type != "private":
        return await message.reply("The <code>/connect</code> command must be used in a private message to the bot.")
        
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Specify a chat ID to connect to. E.g., <code>/connect -1001234567890</code>\nYou must be an admin in that group.")
        
    try:
        target_chat_id = int(args[1])
    except ValueError:
        return await message.reply("Please provide a valid numeric Chat ID.")
        
    try:
        member = await message.bot.get_chat_member(target_chat_id, message.from_user.id)
        if member.status not in ["administrator", "creator"]:
            return await message.reply("You must be an administrator in that chat to connect to it.")
            
        chat = await message.bot.get_chat(target_chat_id)
        chat_title = chat.title
    except TelegramBadRequest:
        return await message.reply("Cannot find that chat. Please ensure the Chat ID is correct and the bot is an admin in that chat.")
        
    await connection_sql.connect(message.from_user.id, target_chat_id)
    await connection_sql.add_history(message.from_user.id, target_chat_id, chat_title or "Unknown")
    
    await message.reply(f"Successfully connected to <b>{html.escape(chat_title or '')}</b>!\nCommands like <code>/filter</code> will now affect that group.")


@connections_router.message(Command("disconnect"))
async def disconnect_chat(message: Message):
    if message.chat.type != "private":
        return await message.reply("The <code>/disconnect</code> command must be used in a private message.")
        
    success = await connection_sql.disconnect(message.from_user.id)
    if success:
        await message.reply("Successfully disconnected from the current chat.")
    else:
        await message.reply("You are not currently connected to any chat.")


@connections_router.message(Command("connection"))
async def check_connection(message: Message):
    if message.chat.type != "private":
        return await message.reply("The <code>/connection</code> command must be used in a private message.")
        
    chat_id, chat_title = await resolve_chat(message)
    if chat_id:
        await message.reply(f"You are currently connected to: <b>{html.escape(chat_title or '')}</b> (<code>{chat_id}</code>)")
    else:
        await message.reply("You are not connected to any chat. Use <code>/connect [chat_id]</code> to connect.")


__help__ = """
<b>Admin Commands:</b>
- <code>/connect [chat_id]</code>: Links your private message with a specific group.
- <code>/disconnect</code>: Unlinks your private message.
- <code>/connection</code>: Shows your currently connected group.
"""

from PglRobot.utils.help_system import register_help
register_help("Connections", __help__)
