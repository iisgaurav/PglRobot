import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

logger = logging.getLogger("debug_middleware")

class DebugMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        if isinstance(event, Update):
            if event.message:
                logger.info(f"Received message from {event.message.from_user.id} in chat {event.message.chat.id} (type: {event.message.chat.type}). Text: {event.message.text}")
        return await handler(event, data)
