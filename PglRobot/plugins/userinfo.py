# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from PglRobot.database import userinfo_sql, trust_sql
from PglRobot.config import Config

userinfo_router = Router()

@userinfo_router.message(Command("setbio"))
async def set_bio(message: Message):
    if len(message.text.split()) < 2:
        return await message.reply("Please provide a bio to set. E.g., <code>/setbio I am a Python developer.</code>")
        
    bio = message.text.split(None, 1)[1]
    if len(bio) > 100:
        return await message.reply("Your bio is too long! Please keep it under 100 characters.")
        
    await userinfo_sql.set_user_bio(message.from_user.id, bio)
    await message.reply("Your bio has been successfully updated!")


@userinfo_router.message(Command("info"))
async def get_info(message: Message):
    target_user = message.from_user
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        
    user_id = target_user.id
    
    text = f"👤 <b>User Info:</b>\n"
    text += f"<b>Name:</b> {target_user.full_name}\n"
    text += f"<b>ID:</b> <code>{user_id}</code>\n"
    if target_user.username:
        text += f"<b>Username:</b> @{target_user.username}\n"
        
    # Check Sudo/Owner
    if str(user_id) == str(Config.OWNER_ID):
        text += f"<b>Status:</b> 👑 Bot Owner\n"
    elif user_id in Config.SUDO_USERS:
        text += f"<b>Status:</b> 🛡️ Sudo User\n"
        
    # Check Trust (if in group)
    if message.chat.type != "private":
        trust_score = await trust_sql.get_trust(message.chat.id, user_id)
        if trust_score > 0:
            text += f"<b>Trust Score:</b> {trust_score}\n"
            
    # Check Bio
    bio = await userinfo_sql.get_user_bio(user_id)
    if bio:
        text += f"<b>Bio:</b> {bio}\n"
        
    # Send profile picture if available
    try:
        photos = await message.bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            photo = photos.photos[0][-1].file_id
            await message.answer_photo(photo, caption=text)
        else:
            await message.reply(text)
    except Exception:
        await message.reply(text)


from aiogram.types import Message, MessageOriginUser

@userinfo_router.message(Command("id"))
async def get_id(message: Message):
    text = ""
    if message.reply_to_message:
        text += f"<b>{message.reply_to_message.from_user.first_name}'s ID:</b> <code>{message.reply_to_message.from_user.id}</code>\n"
        if isinstance(message.reply_to_message.forward_origin, MessageOriginUser):
            text += f"<b>Forwarded User ID:</b> <code>{message.reply_to_message.forward_origin.sender_user.id}</code>\n"
            
    text += f"<b>Your ID:</b> <code>{message.from_user.id}</code>\n"
    
    if message.chat.type != "private":
        text += f"<b>Chat ID:</b> <code>{message.chat.id}</code>\n"
        
    await message.reply(text)


__help__ = """
<b>User Commands:</b>
- /id: Get your ID and the Chat's ID.
- /setbio [text]: Sets a custom biography.
- /info [user]: Displays a detailed information card about the user.
"""

from PglRobot.utils.help_system import register_help
register_help("User Info", __help__)
