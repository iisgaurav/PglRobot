# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from PglRobot.utils.admin_filters import IsAdmin
from PglRobot.utils.help_system import register_help

tagall_router = Router()

ADMIN_OR_OWNER = IsAdmin("can_change_info")

# Dictionary to track ongoing tag-all processes to allow cancellation
# Format: {chat_id: boolean}
TAGGING = {}

@tagall_router.message(
    (F.text.startswith("@all") | F.text.startswith("/tagall")),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER
)
async def tag_all(message: Message):
    chat_id = message.chat.id
    if TAGGING.get(chat_id):
        return await message.reply("A tagging process is already running in this chat. Use <code>/cancel</code> to stop it.")
        
    # Extract the custom message if provided
    text = message.text
    if text.startswith("/tagall"):
        tag_msg = text.replace("/tagall", "").strip()
    else:
        tag_msg = text.replace("@all", "").strip()
        
    if not tag_msg:
        tag_msg = "Attention everyone! 📢"
        
    TAGGING[chat_id] = True
    await message.reply(f"Starting to tag everyone! (Use <code>/cancel</code> to stop).")
    
    try:
        # Aiogram 3 doesn't have a direct get_chat_members() without iterating.
        # But we can try to fetch them if the bot is admin and has rights, 
        # or we might need to rely on the MTProto client for full lists.
        # However, we can use the aiogram bot.get_chat_administrators just as a fallback,
        # but for true members we usually track them or use Telethon.
        # Wait, since PglRobot tracks users in the database via users_sql!
        from PglRobot.database.users_sql import get_chat_users
        
        # This will fetch all users the bot has ever seen in this chat from the local DB!
        chat_users = await get_chat_users(chat_id)
        if not chat_users:
            TAGGING[chat_id] = False
            return await message.reply("I don't have enough users cached in my database for this chat yet.")
            
        chunk_size = 5
        count = 0
        
        for i in range(0, len(chat_users), chunk_size):
            if not TAGGING.get(chat_id):
                break
                
            chunk = chat_users[i:i+chunk_size]
            tags = []
            for u in chunk:
                tags.append(f'<a href="tg://user?id={u.user}">\u200b</a>')
                
            invisible_tags = "".join(tags)
            await message.answer(f"{invisible_tags}{tag_msg}", parse_mode="HTML")
            
            count += len(chunk)
            await asyncio.sleep(2.5)  # Sleep to avoid Telegram rate limits
            
        if TAGGING.get(chat_id):
            await message.answer(f"✅ Successfully tagged {count} members!")
            
    except Exception as e:
        await message.answer(f"An error occurred while tagging: {e}")
    finally:
        TAGGING[chat_id] = False


@tagall_router.message(
    Command("cancel"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER
)
async def cancel_tagall(message: Message):
    chat_id = message.chat.id
    if TAGGING.get(chat_id):
        TAGGING[chat_id] = False
        await message.reply("❌ Tagging process has been cancelled.")
    else:
        await message.reply("There is no tagging process running to cancel.")


__help__ = """
<b>Admin Commands:</b>
- <code>@all</code> or <code>/tagall [message]</code>: Mentions all members in the group by looping through the bot's internal member cache.
- <code>/cancel</code>: Stops an ongoing tag-all process.

<i>Note: The bot chunks mentions (5 per message) and pauses between messages to prevent being rate-limited by Telegram.</i>
"""

register_help("Tag All", __help__)
