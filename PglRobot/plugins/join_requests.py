# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: @VegaCodesHQ (vegacodes.com)
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message, ChatJoinRequest
from PglRobot.database import join_req_sql
from PglRobot.plugins.admin import is_admin

join_requests_router = Router()

@join_requests_router.message(Command("autoapprove"))
async def autoapprove_toggle(message: Message):
    chat_id = message.chat.id
    if message.chat.type == "private":
        return await message.reply("This command is made to be used in groups!")
        
    if not await is_admin(message, message.from_user.id):
        return await message.reply("You need to be an admin to do this.")
        
    args = message.text.split()
    if len(args) < 2:
        status = await join_req_sql.get_auto_approve(chat_id)
        state_str = "ON" if status else "OFF"
        return await message.reply(f"Auto-approve is currently <b>{state_str}</b>.\nTo change it, use <code>/autoapprove on</code> or <code>/autoapprove off</code>.")
        
    toggle = args[1].lower()
    if toggle == "on":
        await join_req_sql.set_auto_approve(chat_id, True)
        await message.reply("Auto-approve is now <b>ON</b>. Any user who requests to join will be automatically approved.")
    elif toggle == "off":
        await join_req_sql.set_auto_approve(chat_id, False)
        await message.reply("Auto-approve is now <b>OFF</b>. Join requests must be manually approved.")
    else:
        await message.reply("Invalid argument. Use <code>on</code> or <code>off</code>.")


@join_requests_router.chat_join_request()
async def on_join_request(update: ChatJoinRequest):
    chat_id = update.chat.id
    
    # Check if auto-approve is enabled
    auto_approve = await join_req_sql.get_auto_approve(chat_id)
    if not auto_approve:
        return
        
    try:
        await update.approve()
        
        # Try to send a welcome PM to the user
        try:
            await update.bot.send_message(
                update.from_user.id,
                f"Welcome to <b>{update.chat.title}</b>! Your request to join has been automatically approved."
            )
        except Exception:
            pass # User might have PMs closed
            
    except Exception as e:
        print(f"Failed to auto-approve user {update.from_user.id} in chat {chat_id}: {e}")


__help__ = """
<b>Admin Commands:</b>
- /autoapprove [on/off]: Toggles auto-approval of join requests.
"""

from PglRobot.utils.help_system import register_help
register_help("Join Requests", __help__)
