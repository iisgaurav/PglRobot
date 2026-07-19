# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from PglRobot.database import forceSubscribe_sql, approve_sql, trust_sql
from PglRobot.plugins.admin import is_admin
from aiogram.exceptions import TelegramBadRequest

fsub_router = Router()

@fsub_router.message(Command("fsub"))
async def set_fsub(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups!")
        
    if not await is_admin(message, message.from_user.id):
        return await message.reply("You need to be an admin to do this.")
        
    args = message.text.split()
    if len(args) < 2:
        curr_fsub = await forceSubscribe_sql.get_fsub(chat_id)
        if curr_fsub:
            return await message.reply(f"Current Force Subscribe channel is: <code>{curr_fsub}</code>\nTo disable it, use <code>/fsub off</code>")
        return await message.reply("Specify a channel username or ID to force users to join. E.g., <code>/fsub @MyChannel</code>")
        
    channel = args[1]
    if channel.lower() == "off":
        await forceSubscribe_sql.remove_fsub(chat_id)
        return await message.reply("Force Subscribe has been disabled.")
        
    # Test if bot is admin in the channel by trying to get its own member status
    try:
        bot_member = await message.bot.get_chat_member(channel, message.bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            return await message.reply("The bot is not an administrator in that channel! Please add the bot as an admin to the channel first so it can check member statuses.")
    except TelegramBadRequest:
        return await message.reply("Could not find that channel, or the bot is not added to it. Ensure you used the correct username/ID and that the bot is an admin there.")
        
    await forceSubscribe_sql.set_fsub(chat_id, channel)
    await message.reply(f"Force Subscribe enabled! Users must now join <code>{channel}</code> to speak in this group.")


from aiogram.dispatcher.event.bases import SkipHandler

# Global FSub Interceptor
@fsub_router.message()
async def fsub_interceptor(message: Message):
    if message.chat.type == "private" or not message.from_user:
        raise SkipHandler()
        
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Fast paths out
    channel = await forceSubscribe_sql.get_fsub(chat_id)
    if not channel:
        raise SkipHandler()
        
    if await is_admin(message, user_id):
        raise SkipHandler()
    if await approve_sql.is_approved(chat_id, user_id):
        raise SkipHandler()
    if await trust_sql.get_trust(chat_id, user_id) > 0:
        raise SkipHandler()
        
    # Check if user is in channel
    try:
        member = await message.bot.get_chat_member(channel, user_id)
        if member.status in ["left", "kicked", "restricted"]:
            raise ValueError("Not in channel")
    except Exception:
        # Not in channel or API error -> delete message
        try:
            await message.delete()
        except Exception:
            pass # No rights
            
        # Send warning
        channel_link = f"https://t.me/{channel.replace('@', '')}" if channel.startswith("@") else channel
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Join Channel", url=channel_link)]
        ])
        
        warn_msg = await message.answer(
            f"Hello {message.from_user.first_name},\nYou must join our channel to send messages here!",
            reply_markup=kb
        )
        # but for now, we'll leave it or rely on purge.
        return
        
    raise SkipHandler()


__help__ = """
<b>Admin Commands:</b>
- /fsub [channel]: Sets the Force Subscribe channel (Bot must be admin in channel).
- /fsub off: Disables Force Subscribe.
"""

from PglRobot.utils.help_system import register_help
register_help("Force Subscribe", __help__)
