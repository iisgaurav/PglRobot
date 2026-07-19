from aiogram.filters import Filter
from aiogram.types import Message, ChatMemberOwner, ChatMemberAdministrator

from PglRobot.config import Config


class IsSudoUser(Filter):
    """
    Filter that only passes for the bot owner and sudo users.
    Works in both groups and private chats.
    """
    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False
        return message.from_user.id in Config.SUDO_USERS


class IsAdmin(Filter):
    """
    Filter to check if the user is an admin or owner of the chat.
    Optionally checks if they have a specific permission.
    Always passes for group owners regardless of permission check.
    """
    def __init__(self, permission: str | None = None):
        self.permission = permission

    async def __call__(self, message: Message) -> bool:
        if message.chat.type == "private":
            return True

        if not message.from_user:
            return False

        # Sudo users bypass all admin checks (matching oldbot behavior)
        if message.from_user.id in Config.SUDO_USERS:
            return True

        try:
            member = await message.chat.get_member(message.from_user.id)
            print(f"DEBUG IsAdmin: User {message.from_user.id} is {member.status}")
        except Exception as e:
            print(f"DEBUG IsAdmin Error: {e}")
            return False

        # Owners have all permissions unconditionally
        if isinstance(member, ChatMemberOwner):
            print(f"DEBUG IsAdmin: User is owner. Allowed.")
            return True

        if isinstance(member, ChatMemberAdministrator):
            if self.permission:
                val = getattr(member, self.permission, None)
                print(f"DEBUG IsAdmin: Permission {self.permission} = {val}")
                # Treat None as True — Telegram omits fields that are True
                # when the admin has all permissions granted
                if val is True or val is None:
                    return True
                return False
            print(f"DEBUG IsAdmin: No specific permission required. Allowed.")
            return True

        print(f"DEBUG IsAdmin: User is regular member. Denied.")
        return False


class BotCan(Filter):
    """
    Filter to check if the bot itself has a specific permission in the chat.
    """
    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(self, message: Message) -> bool:
        if message.chat.type == "private":
            return True

        try:
            bot_member = await message.chat.get_member(message.bot.id)
        except Exception:
            return False

        if isinstance(bot_member, ChatMemberOwner):
            return True

        if isinstance(bot_member, ChatMemberAdministrator):
            val = getattr(bot_member, self.permission, None)
            return val is True or val is None

        return False


async def check_if_admin(chat, user_id: int) -> bool:
    """Helper to check if a specific user is an admin in a chat."""
    if chat.type == "private":
        return True
    try:
        member = await chat.get_member(user_id)
        return isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))
    except Exception:
        return False
