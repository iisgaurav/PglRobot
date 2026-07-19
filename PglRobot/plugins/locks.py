# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from PglRobot.database import locks_sql, approve_sql, trust_sql
from PglRobot.plugins.admin import is_admin

locks_router = Router()

LOCK_TYPES = {
    "audio": "audio",
    "voice": "voice",
    "contact": "contact",
    "video": "video",
    "document": "document",
    "photo": "photo",
    "sticker": "sticker",
    "gif": "gif",
    "url": "url",
    "bots": "bots",
    "forward": "forward",
    "game": "game",
    "location": "location"
}

@locks_router.message(Command("lock"))
async def lock_type(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups!")
    
    if not await is_admin(message, message.from_user.id):
        return await message.reply("You need to be an admin to do this.")
        
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("You need to specify what to lock. E.g., <code>/lock url</code> or <code>/lock photo</code>")
        
    ltype = args[1].lower()
    if ltype not in LOCK_TYPES:
        return await message.reply(f"Invalid lock type. Available locks: {', '.join(LOCK_TYPES.keys())}")
        
    await locks_sql.update_lock(chat_id, ltype, True)
    await message.reply(f"Locked <code>{ltype}</code> in this group.")


@locks_router.message(Command("unlock"))
async def unlock_type(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups!")
    
    if not await is_admin(message, message.from_user.id):
        return await message.reply("You need to be an admin to do this.")
        
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("You need to specify what to unlock. E.g., <code>/unlock url</code>")
        
    ltype = args[1].lower()
    if ltype not in LOCK_TYPES:
        return await message.reply(f"Invalid lock type. Available locks: {', '.join(LOCK_TYPES.keys())}")
        
    await locks_sql.update_lock(chat_id, ltype, False)
    await message.reply(f"Unlocked <code>{ltype}</code> in this group.")


@locks_router.message(Command("locks"))
async def view_locks(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups!")
        
    perms = await locks_sql.get_locks(chat_id)
    text = f"<b>Locks in {message.chat.title}:</b>\n\n"
    for ltype in LOCK_TYPES.keys():
        is_locked = getattr(perms, ltype, False)
        status = "🔒 Locked" if is_locked else "🔓 Unlocked"
        text += f"<b>{ltype.capitalize()}:</b> {status}\n"
        
    await message.reply(text)

# Global interceptor
@locks_router.message()
async def intercept_locks(message: Message):
    if message.chat.type == "private" or not message.from_user:
        return
        
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    from aiogram.dispatcher.event.bases import SkipHandler
    # Check bypasses
    if await is_admin(message, user_id):
        raise SkipHandler()
    if await approve_sql.is_approved(chat_id, user_id):
        raise SkipHandler()
    if await trust_sql.get_trust(chat_id, user_id) > 0:
        raise SkipHandler()
        
    perms = await locks_sql.get_locks(chat_id)
    
    # Evaluate message against locks
    should_delete = False
    
    if perms.audio and message.audio:
        should_delete = True
    elif perms.voice and message.voice:
        should_delete = True
    elif perms.contact and message.contact:
        should_delete = True
    elif perms.video and (message.video or message.video_note):
        should_delete = True
    elif perms.document and message.document:
        should_delete = True
    elif perms.photo and message.photo:
        should_delete = True
    elif perms.sticker and message.sticker:
        should_delete = True
    elif perms.gif and message.animation:
        should_delete = True
    elif perms.forward and message.forward_date:
        should_delete = True
    elif perms.game and message.game:
        should_delete = True
    elif perms.location and message.location:
        should_delete = True
    elif perms.url and message.entities:
        for ent in message.entities:
            if ent.type in ["url", "text_link"]:
                should_delete = True
                break
                
    if should_delete:
        try:
            await message.delete()
        except Exception:
            pass # Bot might not have delete rights
        return
        
    raise SkipHandler()


__help__ = """
<b>Admin Commands:</b>
- /lock [type]: Locks a specific media type (e.g., url, photo, audio).
- /unlock [type]: Unlocks the media type.
- /locks: Shows current group locks.
"""

from PglRobot.utils.help_system import register_help
register_help("Locks", __help__)
