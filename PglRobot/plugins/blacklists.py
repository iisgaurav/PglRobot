# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: @VegaCodesHQ (vegacodes.com)
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import re
from PglRobot.database import blacklist_sql, approve_sql, trust_sql
from PglRobot.plugins.admin import is_admin

blacklists_router = Router()

@blacklists_router.message(Command("addblacklist"))
async def add_blacklist(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups!")
        
    if not await is_admin(message, message.from_user.id):
        return await message.reply("You need to be an admin to do this.")
        
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Specify a word to blacklist. E.g., <code>/addblacklist spamword</code>")
        
    word = args[1].lower()
    await blacklist_sql.add_to_blacklist(chat_id, word)
    await message.reply(f"Added <code>{word}</code> to the blacklist in this group. Any message containing this word will be deleted.")


@blacklists_router.message(Command("unblacklist"))
async def rem_blacklist(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups!")
        
    if not await is_admin(message, message.from_user.id):
        return await message.reply("You need to be an admin to do this.")
        
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Specify a word to unblacklist. E.g., <code>/unblacklist spamword</code>")
        
    word = args[1].lower()
    removed = await blacklist_sql.rm_from_blacklist(chat_id, word)
    if removed:
        await message.reply(f"Removed <code>{word}</code> from the blacklist.")
    else:
        await message.reply("That word is not in the blacklist.")


@blacklists_router.message(Command("blacklists"))
async def view_blacklists(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups!")
        
    if not await is_admin(message, message.from_user.id):
        return await message.reply("You need to be an admin to do this.")
        
    words = await blacklist_sql.get_chat_blacklist(chat_id)
    if not words:
        return await message.reply("There are no blacklisted words in this group.")
        
    text = "<b>Blacklisted Words:</b>\n"
    for w in words:
        text += f"- <code>{w}</code>\n"
        
    await message.reply(text)

# Global interceptor
from aiogram.dispatcher.event.bases import SkipHandler

@blacklists_router.message()
async def intercept_blacklists(message: Message):
    text = message.text or message.caption
    if not text or message.chat.type == "private" or not message.from_user:
        raise SkipHandler()
        
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    words = await blacklist_sql.get_chat_blacklist(chat_id)
    if not words:
        raise SkipHandler()
        
    # Check bypasses
    if await is_admin(message, user_id):
        raise SkipHandler()
    if await approve_sql.is_approved(chat_id, user_id):
        raise SkipHandler()
    if await trust_sql.get_trust(chat_id, user_id) > 0:
        raise SkipHandler()
        
    text_lower = text.lower()
    for word in words:
        # Check if blacklisted word is in the message (regex for whole word matching to prevent accidental bans)
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_lower) or word in text_lower:
            try:
                await message.delete()
                # Optional: send a warning
                # await message.answer(f"Deleted message from {message.from_user.first_name} for containing a blacklisted word.")
            except Exception:
                pass
            return # Swallow if dirty
    
    raise SkipHandler()


__help__ = """
<b>Admin Commands:</b>
- /addblacklist [word]: Adds a word to the chat blacklist.
- /unblacklist [word]: Removes the word.
- /blacklists: Shows all blacklisted words.
"""

from PglRobot.utils.help_system import register_help
register_help("Blacklists", __help__)
