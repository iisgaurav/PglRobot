from typing import final, override
from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.enums import ChatMemberStatus
from PglRobot.config import Config

@final
class IsAdmin(BaseFilter):
    def __init__(self, can_restrict_members: bool = False, can_pin_messages: bool = False, can_promote_members: bool = False):
        self.can_restrict_members = can_restrict_members
        self.can_pin_messages = can_pin_messages
        self.can_promote_members = can_promote_members

    @override
    async def __call__(self, message: Message) -> bool:
        if message.chat.type == "private":
            return True
            
        if not message.from_user:
            return False
            
        user_id = message.from_user.id
        
        # Superusers bypass normal checks
        if user_id in Config.SUDO_USERS or user_id in Config.DEV_USERS or user_id == Config.OWNER_ID:
            return True
            
        member = await message.chat.get_member(user_id)
        if member.status == ChatMemberStatus.CREATOR:
            return True
            
        if member.status != ChatMemberStatus.ADMINISTRATOR:
            return False
            
        # Check specific permissions if requested
        if self.can_restrict_members and getattr(member, 'can_restrict_members', False) is False:
            return False
            
        if self.can_pin_messages and getattr(member, 'can_pin_messages', False) is False:
            return False
            
        if self.can_promote_members and getattr(member, 'can_promote_members', False) is False:
            return False
            
        return True

@final
class IsSudo(BaseFilter):
    @override
    async def __call__(self, message: Message) -> bool:
        if not message.from_user:
            return False
        user_id = message.from_user.id
        return user_id in Config.SUDO_USERS or user_id in Config.DEV_USERS or user_id == Config.OWNER_ID

