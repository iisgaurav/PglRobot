# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import aiohttp
from PglRobot.database import nsfw_sql
from PglRobot.plugins.admin import is_admin
from PglRobot.config import Config

nsfw_router = Router()

@nsfw_router.message(Command("nsfw"))
async def toggle_nsfw(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups!")
        
    if not await is_admin(message, message.from_user.id):
        return await message.reply("You need to be an admin to do this.")
        
    if not Config.SIGHTENGINE_API_USER or not Config.SIGHTENGINE_API_SECRET:
        return await message.reply("⚠️ NSFW Detection requires Sightengine API keys in <code>config.py</code>.\nPlease add <code>SIGHTENGINE_API_USER</code> and <code>SIGHTENGINE_API_SECRET</code>.")
        
    args = message.text.split()
    if len(args) < 2:
        status = await nsfw_sql.is_nsfw(chat_id)
        state_str = "ON" if status else "OFF"
        return await message.reply(f"NSFW Detection is currently <b>{state_str}</b>.\nTo change it, use <code>/nsfw on</code> or <code>/nsfw off</code>.")
        
    toggle = args[1].lower()
    if toggle == "on":
        await nsfw_sql.set_nsfw(chat_id)
        await message.reply("NSFW Detection is now <b>ON</b>. I will scan and delete inappropriate photos.")
    elif toggle == "off":
        await nsfw_sql.rem_nsfw(chat_id)
        await message.reply("NSFW Detection is now <b>OFF</b>.")
    else:
        await message.reply("Invalid argument. Use <code>on</code> or <code>off</code>.")


# Global Interceptor for Photos
from aiogram.dispatcher.event.bases import SkipHandler

@nsfw_router.message()
async def check_nsfw(message: Message):
    if message.chat.type == "private" or not message.from_user or not message.photo:
        raise SkipHandler()
        
    if not Config.SIGHTENGINE_API_USER or not Config.SIGHTENGINE_API_SECRET:
        raise SkipHandler()
        
    chat_id = message.chat.id
    if not await nsfw_sql.is_nsfw(chat_id):
        raise SkipHandler()
        
    # Get the largest photo resolution
    photo = message.photo[-1]
    
    try:
        # Get the direct download URL from Telegram
        file = await message.bot.get_file(photo.file_id)
        file_url = f"https://api.telegram.org/file/bot{Config.TOKEN}/{file.file_path}"
        
        # Send to Sightengine
        params = {
            'models': 'nudity-2.0,gore',
            'api_user': Config.SIGHTENGINE_API_USER,
            'api_secret': Config.SIGHTENGINE_API_SECRET,
            'url': file_url
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.sightengine.com/1.0/check.json', params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "success":
                        nudity = data.get("nudity", {})
                        gore = data.get("gore", {})
                        
                        # Check thresholds (e.g. > 50% probability of nudity/gore)
                        is_nsfw = False
                        
                        # Sightengine Nudity 2.0 classes: safe, suggestive, sexual_activity, sexual_display, erotica
                        if nudity.get("sexual_activity", 0) > 0.5 or nudity.get("sexual_display", 0) > 0.5 or nudity.get("erotica", 0) > 0.6:
                            is_nsfw = True
                            
                        if gore.get("prob", 0) > 0.6:
                            is_nsfw = True
                            
                        if is_nsfw:
                            await message.delete()
                            await message.answer(f"Deleted a photo from {message.from_user.first_name} because it was detected as NSFW/Gore.")
                            return # Swallow dirty message
                            
    except Exception as e:
        print(f"NSFW Detection Error: {e}")
        
    raise SkipHandler()


__help__ = """
<b>Admin Commands:</b>
- /nsfw [on/off]: Toggles NSFW image scanning.
"""

from PglRobot.utils.help_system import register_help
register_help("NSFW", __help__)
