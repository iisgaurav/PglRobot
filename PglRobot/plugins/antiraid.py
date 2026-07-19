# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: @VegaCodesHQ (vegacodes.com)
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.exceptions import TelegramBadRequest

from PglRobot.database import antiraid_sql as sql
from PglRobot.utils.admin_filters import IsAdmin, BotCan
from PglRobot.utils.help_system import register_help

antiraid_router = Router()

ADMIN_OR_OWNER = IsAdmin("can_restrict_members")
BOT_CAN_RESTRICT = BotCan("can_restrict_members")


@antiraid_router.message(
    Command("antiraid"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER
)
async def toggle_antiraid(message: Message, command: CommandObject):
    args = command.args
    if not args:
        status = await sql.get_antiraid(message.chat.id)
        state_str = "ON" if status else "OFF"
        return await message.reply(f"Raid mode is currently <b>{state_str}</b> in this chat.\nTo change it, use <code>/antiraid on</code> or <code>/antiraid off</code>.")
        
    toggle = args.lower()
    if toggle in ["on", "yes", "true"]:
        await sql.set_antiraid(message.chat.id, True)
        await message.reply("🚨 <b>Raid Mode Enabled!</b>\nAny user who joins this group will be instantly kicked until raid mode is disabled.")
    elif toggle in ["off", "no", "false"]:
        await sql.set_antiraid(message.chat.id, False)
        await message.reply("✅ <b>Raid Mode Disabled!</b>\nUsers can now join the group normally.")
    else:
        await message.reply("Invalid argument. Use <code>on</code> or <code>off</code>.")


@antiraid_router.message(F.new_chat_members)
async def handle_new_members(message: Message, bot: Bot):
    chat = message.chat
    
    # Check if raid mode is active
    if not await sql.get_antiraid(chat.id) or not message.new_chat_members:
        return
        
    try:
        # Check if the bot actually has rights to kick
        bot_member = await bot.get_chat_member(chat.id, bot.id)
        if hasattr(bot_member, "can_restrict_members") and not getattr(bot_member, "can_restrict_members"):
            return
            
        kicked_count = 0
        for new_user in message.new_chat_members:
            # Don't try to kick other bots or admins if they were added
            if new_user.is_bot:
                continue
                
            # Kick the user (ban then unban)
            await bot.ban_chat_member(chat.id, new_user.id)
            await bot.unban_chat_member(chat.id, new_user.id)
            kicked_count += 1
            
        if kicked_count > 0:
            # Optionally delete the "user joined" message to keep chat clean during raid
            try:
                await message.delete()
            except TelegramBadRequest:
                pass
                
    except TelegramBadRequest:
        pass


__help__ = """
<b>Admin Commands:</b>
- <code>/antiraid [on/off]</code>: Toggles Raid Mode. When enabled, anyone who joins the group will be instantly kicked. Use this to protect your group during a bot attack!
"""

register_help("Anti-Raid", __help__)
