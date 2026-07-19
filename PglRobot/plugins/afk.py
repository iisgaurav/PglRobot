# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import random
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable
from collections.abc import Awaitable
from PglRobot.database import afk_sql as sql

afk_router = Router()

@afk_router.message(Command("afk"))
async def set_afk(message: Message, command: CommandObject):
    if not message.from_user:
        return
        
    reason: str = command.args if command.args is not None else ""
    notice = ""
    if len(reason) > 100:
        reason = reason[:100]
        notice = "\nYour AFK reason was shortened to 100 characters."
        
    await sql.set_afk(message.from_user.id, reason)
    await message.reply(f"{message.from_user.first_name} is now away!{notice}")

@afk_router.message(F.text.re_match(r"(?i)^brb(.*)$"))
async def set_afk_brb(message: Message):
    if not message.from_user:
        return
        
    text = message.text or ""
    reason = text[3:].strip() if len(text) > 3 else ""
    notice = ""
    if len(reason) > 100:
        reason = reason[:100]
        notice = "\nYour AFK reason was shortened to 100 characters."
        
    await sql.set_afk(message.from_user.id, reason)
    await message.reply(f"{message.from_user.first_name} is now away!{notice}")

class AFKMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, object]], Awaitable[object]],
        event: TelegramObject,
        data: dict[str, object]
    ) -> object:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)
            
        message = event
        user_id = message.from_user.id
        
        # 1. Check if the sender was AFK
        if await sql.is_afk(user_id):
            removed = await sql.rm_afk(user_id)
            if removed:
                options = [
                    "{} is here!",
                    "{} is back!",
                    "{} is now in the chat!",
                    "{} is awake!",
                    "{} is back online!",
                    "{} is finally here!",
                    "Welcome back! {}",
                    "Where is {}?\nIn the chat!"
                ]
                chosen = random.choice(options)
                await message.reply(chosen.format(message.from_user.first_name))
                
        # 2. Check if the sender mentioned an AFK user
        # Check reply first
        if message.reply_to_message and message.reply_to_message.from_user:
            replied_user = message.reply_to_message.from_user
            if replied_user.id != user_id and await sql.is_afk(replied_user.id):
                afk_data = await sql.check_afk_status(replied_user.id)
                if afk_data and afk_data.reason:
                    await message.reply(f"{replied_user.first_name} is afk.\nReason: <code>{afk_data.reason}</code>")
                else:
                    await message.reply(f"{replied_user.first_name} is afk.")
                    
        # Check mentions in text
        if message.entities:
            checked_users = set()
            for entity in message.entities:
                if entity.type == "text_mention" and entity.user:
                    mentioned_id = entity.user.id
                    if mentioned_id == user_id or mentioned_id in checked_users:
                        continue
                    checked_users.add(mentioned_id)
                    
                    if await sql.is_afk(mentioned_id):
                        afk_data = await sql.check_afk_status(mentioned_id)
                        if afk_data and afk_data.reason:
                            await message.reply(f"{entity.user.first_name} is afk.\nReason: <code>{afk_data.reason}</code>")
                        else:
                            await message.reply(f"{entity.user.first_name} is afk.")
                            
        return await handler(event, data)

# Register the middleware
afk_router.message.middleware(AFKMiddleware())

__help__ = """
*AFK Commands:*
 • <code>/afk <reason></code>: Mark yourself as AFK.
 • <code>brb <reason></code>: Same as the afk command, but without a slash.
When marked as AFK, any mentions will be replied to with a message to say you're not available!
"""
from PglRobot.utils.help_system import register_help
register_help("AFK", __help__)
