# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.utils.deep_linking import create_start_link

from PglRobot.utils.admin_filters import IsAdmin
from PglRobot.database import rules_sql as sql

rules_router = Router()
ADMIN_OR_OWNER = IsAdmin("can_change_info")

@rules_router.message(Command("rules", "setrules", "clearrules"), F.chat.type == "private")
async def pm_fallback(message: Message):
    await message.reply("This command can only be used in groups.")


@rules_router.message(Command("rules"), F.chat.type.in_({"group", "supergroup"}))
async def get_rules_group(message: Message, bot: Bot):
    chat_id = message.chat.id
    rules = await sql.get_rules(chat_id)
    
    if not rules:
        return await message.reply("The group admins haven't set any rules for this chat yet. This probably doesn't mean it's lawless though...!")

    # Deep link to PM
    # Payload format: rules_chatId
    payload = f"rules_{str(chat_id).replace('-', '_')}"
    link = await create_start_link(bot, payload, encode=False)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Rules", url=link)]
    ])
    
    await message.reply("Please click the button below to see the rules.", reply_markup=keyboard)


@rules_router.message(CommandStart(deep_link=True))
async def get_rules_pm(message: Message, command: CommandObject, bot: Bot):
    # This acts as a handler for the deep link in PM
    payload = command.args
    if payload and payload.startswith("rules_"):
        chat_id_str = payload.replace("rules_", "").replace("_", "-")
        try:
            chat_id = int(chat_id_str)
        except ValueError:
            return await message.reply("Invalid chat ID in rules link.")
            
        try:
            chat = await bot.get_chat(chat_id)
        except Exception:
            return await message.reply("I couldn't find that chat. Make sure I'm still in it!")
            
        rules = await sql.get_rules(chat_id)
        if rules:
            text = f"The rules for <b>{chat.title}</b> are:\n\n{rules}"
            await message.reply(text)
        else:
            await message.reply("The group admins haven't set any rules for this chat yet.")


@rules_router.message(Command("setrules"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER)
async def set_rules(message: Message, command: CommandObject):
    if not command.args:
        return await message.reply("You need to provide the rules text! Example: /setrules 1. Be nice.")
        
    await sql.set_rules(message.chat.id, command.args)
    await message.reply("Successfully set rules for this group.")


@rules_router.message(Command("clearrules"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER)
async def clear_rules(message: Message):
    await sql.set_rules(message.chat.id, "")
    await message.reply("Successfully cleared rules!")

__help__ = """
<b>Rules Commands:</b>
- <code>/rules</code>: Get the rules for this chat.
- <code>/setrules <text></code>: Set the rules for this chat.
- <code>/clearrules</code>: Clear the rules for this chat.
"""
from PglRobot.utils.help_system import register_help
register_help("Rules", __help__)
