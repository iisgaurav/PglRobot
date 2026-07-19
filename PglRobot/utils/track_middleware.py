import asyncio
import time
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from typing import Callable
from collections.abc import Awaitable
from PglRobot.database.users_sql import update_user

class TrackUsersMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        # Cache to store (user_id, chat_id) tuples and their last seen timestamp
        # This prevents spamming the database with the same user in the same chat
        self.cache = {}
        # Cache expiration time in seconds (e.g., 5 minutes)
        self.cache_ttl = 300 
        self._lock = asyncio.Lock()

    async def _clean_cache(self):
        now = time.time()
        # Clean up old entries from the cache to prevent memory leaks
        async with self._lock:
            keys_to_delete = [
                key for key, timestamp in self.cache.items() 
                if now - timestamp > self.cache_ttl
            ]
            for key in keys_to_delete:
                del self.cache[key]

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, object]], Awaitable[object]],
        event: TelegramObject,
        data: dict[str, object]
    ) -> object:
        if not isinstance(event, Update):
            return await handler(event, data)

            
        # We need to extract the user and chat info from the event
        user = None
        chat = None

        if event.message:
            user = event.message.from_user
            chat = event.message.chat
        elif event.callback_query:
            user = event.callback_query.from_user
            if event.callback_query.message:
                chat = event.callback_query.message.chat
        elif event.my_chat_member:
            user = event.my_chat_member.from_user
            chat = event.my_chat_member.chat
        elif event.chat_member:
            user = event.chat_member.from_user
            chat = event.chat_member.chat
        
        if user:
            user_id = user.id
            username = user.username
            chat_id = chat.id if chat else None
            chat_name = chat.title if chat and chat.type != "private" else None
            
            # Use 0 or None as a generic marker for private/PM chats if chat is None
            cache_key = (user_id, chat_id)
            now = time.time()

            should_update = False
            async with self._lock:
                if cache_key not in self.cache or (now - self.cache[cache_key]) > self.cache_ttl:
                    self.cache[cache_key] = now
                    should_update = True
                    
            if should_update:
                # We do this asynchronously without blocking the event handler if possible, 
                # but await it for safety since SQLAlchemy needs a session.
                try:
                    await update_user(user_id, username, chat_id, chat_name)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Failed to track user {user_id} in chat {chat_id}: {e}")

                # Periodically clean the cache (1 in 100 chance to run)
                import random
                if random.random() < 0.01:
                    asyncio.create_task(self._clean_cache())
                    
        return await handler(event, data)
