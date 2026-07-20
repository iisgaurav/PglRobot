# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router
import html
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import Message
import re
from PglRobot.database import cust_filters_sql
from PglRobot.plugins.admin import is_admin
from PglRobot.plugins.connections import resolve_chat

filters_router = Router()

@filters_router.message(Command("filter"))
async def add_custom_filter(message: Message):
    chat_id, chat_title = await resolve_chat(message)
    if not chat_id:
        return await message.reply("You must use this command in a group or connect to one in PM.")
        
    if not await is_admin(message, message.from_user.id, chat_id=chat_id):
        return await message.reply("You need to be an admin to do this.")
        
    args = message.text.split(None, 2)
    if len(args) < 2:
        return await message.reply("Specify a keyword. E.g., <code>/filter hello Hi there!</code> or reply to a sticker/photo with <code>/filter keyword</code>")
        
    keyword = args[1].lower()
    
    reply_text = None
    file_type = 1 # 1=text
    file_id = None
    has_buttons = False # (Buttons not implemented yet, just boilerplate)
    
    if message.reply_to_message:
        rm = message.reply_to_message
        reply_text = rm.text or rm.caption or ""
        
        if rm.photo:
            file_type = 2
            file_id = rm.photo[-1].file_id
        elif rm.video:
            file_type = 3
            file_id = rm.video.file_id
        elif rm.audio:
            file_type = 4
            file_id = rm.audio.file_id
        elif rm.voice:
            file_type = 5
            file_id = rm.voice.file_id
        elif rm.document:
            file_type = 6
            file_id = rm.document.file_id
        elif rm.sticker:
            file_type = 7
            file_id = rm.sticker.file_id
        elif rm.animation:
            file_type = 8
            file_id = rm.animation.file_id
    else:
        if len(args) < 3:
            return await message.reply("You need to provide the reply text or reply to a media message!")
        reply_text = args[2]
        
    await cust_filters_sql.add_filter(chat_id, keyword, reply_text, file_type, file_id, has_buttons)
    await message.reply(f"Filter added for <code>{html.escape(keyword or '')}</code> in <b>{html.escape(chat_title or '')}</b>!")


@filters_router.message(Command("stop"))
async def remove_custom_filter(message: Message):
    chat_id, chat_title = await resolve_chat(message)
    if not chat_id:
        return await message.reply("You must use this command in a group or connect to one in PM.")
        
    if not await is_admin(message, message.from_user.id, chat_id=chat_id):
        return await message.reply("You need to be an admin to do this.")
        
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Specify a keyword to stop. E.g., <code>/stop hello</code>")
        
    keyword = args[1].lower()
    removed = await cust_filters_sql.remove_filter(chat_id, keyword)
    if removed:
        await message.reply(f"Filter for <code>{html.escape(keyword or '')}</code> removed in <b>{html.escape(chat_title or '')}</b>.")
    else:
        await message.reply("That filter does not exist.")


@filters_router.message(Command("filters"))
async def list_filters(message: Message):
    chat_id, chat_title = await resolve_chat(message)
    if not chat_id:
        return await message.reply("You must use this command in a group or connect to one in PM.")
        
    filters = await cust_filters_sql.get_all_filters(chat_id)
    if not filters:
        return await message.reply(f"There are no custom filters in <b>{html.escape(chat_title or '')}</b>.")
        
    text = f"<b>Filters in {html.escape(chat_title or '')}:</b>\n"
    for f in filters:
        text += f"- <code>{f.keyword}</code>\n"
        
    await message.reply(text)



# Global Interceptor for Filters
@filters_router.message()
async def intercept_filters(message: Message):
    if message.chat.type == "private" or not message.from_user:
        raise SkipHandler()
        
    text = message.text or message.caption
    if not text:
        raise SkipHandler()
        
    chat_id = message.chat.id
    filters = await cust_filters_sql.get_all_filters(chat_id)
    if not filters:
        raise SkipHandler()
        
    text_lower = text.lower()
    for f in filters:
        # Check if keyword exactly matches a word or the entire text
        # E.g. trigger word "hello" matches "hello guys" but not "othello"
        pattern = r'\b' + re.escape(f.keyword) + r'\b'
        if re.search(pattern, text_lower) or f.keyword == text_lower:
            
            # Send the reply!
            if f.file_type == 1:
                await message.answer(f.reply_text or "")
            elif f.file_type == 2:
                await message.answer_photo(str(f.file_id), caption=f.reply_text)
            elif f.file_type == 3:
                await message.answer_video(str(f.file_id), caption=f.reply_text)
            elif f.file_type == 4:
                await message.answer_audio(str(f.file_id), caption=f.reply_text)
            elif f.file_type == 5:
                await message.answer_voice(str(f.file_id), caption=f.reply_text)
            elif f.file_type == 6:
                await message.answer_document(str(f.file_id), caption=f.reply_text)
            elif f.file_type == 7:
                await message.answer_sticker(str(f.file_id))
            elif f.file_type == 8:
                await message.answer_animation(str(f.file_id), caption=f.reply_text)
                
            break # Only trigger the first matched filter to avoid spam
    else:
        # Loop finished without breaking, meaning no filter triggered
        raise SkipHandler()


__help__ = """
<b>Admin Commands:</b>
- /filter [keyword] [reply]: Adds a custom response trigger.
- /stop [keyword]: Deletes the custom filter.
- /filters: Lists all active filters.
"""

from PglRobot.utils.help_system import register_help
register_help("Filters", __help__)
