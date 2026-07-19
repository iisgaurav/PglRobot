from typing import Callable
from collections.abc import Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from PglRobot.database.disable_sql import is_command_disabled

class DisableMiddleware(BaseMiddleware):
    """
    Middleware that intercepts all incoming messages and checks if they contain
    a command that has been disabled in the current chat.
    If the command is disabled, the message is quietly dropped before any plugin sees it.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, object]], Awaitable[object]],
        event: TelegramObject,
        data: dict[str, object]
    ) -> object:
        if not isinstance(event, Update):
            return await handler(event, data)

        # We only care about message events that contain text
        if event.message and event.message.text and event.message.text.startswith('/'):
            chat_id = event.message.chat.id
            
            # Extract the pure command without the slash, arguments, or @botname
            # Example: /disable@MyBot args -> disable
            command_parts = event.message.text.split()[0].split('@')
            command = command_parts[0][1:].lower()
            
            if await is_command_disabled(chat_id, command):
                # The command is disabled in this chat.
                # Returning None means we swallow the event and stop propagation.
                return None
                
        # If not disabled (or not a command), proceed normally
        return await handler(event, data)
