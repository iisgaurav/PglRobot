# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import html
from aiogram import Router, F, Bot
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from aiogram.exceptions import TelegramBadRequest

from PglRobot.database import antiflood_sql as sql
from PglRobot.utils.admin_filters import IsAdmin, BotCan
from PglRobot.utils.help_system import register_help
from PglRobot.utils.time_parser import extract_time

antiflood_router = Router()

ADMIN_OR_OWNER = IsAdmin("can_restrict_members")
BOT_CAN_RESTRICT = BotCan("can_restrict_members")


@antiflood_router.message(
    Command("setflood"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER
)
async def set_flood(message: Message, command: CommandObject):
    args = command.args
    if not args:
        limit = await sql.get_flood_limit(message.chat.id)
        if limit == 0:
            return await message.reply("Antiflood is currently <b>disabled</b>.\nTo enable, use <code>/setflood <number></code>.")
        else:
            return await message.reply(f"Antiflood is currently set to <b>{limit}</b> consecutive messages.")
            
    if args.lower() in ["off", "disable", "0"]:
        await sql.set_flood(message.chat.id, 0)
        return await message.reply("Antiflood has been <b>disabled</b>.")
        
    try:
        limit = int(args.split()[0])
        if limit < 3 and limit != 0:
            return await message.reply("Antiflood limit must be at least 3 messages.")
        await sql.set_flood(message.chat.id, limit)
        await message.reply(f"Antiflood has been updated and set to <b>{limit}</b> consecutive messages.")
    except ValueError:
        await message.reply("Please provide a valid number.")


@antiflood_router.message(
    Command("setfloodmode"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER
)
async def set_flood_mode(message: Message, command: CommandObject):
    args = command.args
    if not args:
        flood_type, value = await sql.get_flood_setting(message.chat.id)
        types = {1: "ban", 2: "kick", 3: "mute", 4: "tempban", 5: "tempmute"}
        mode = types.get(flood_type, "ban")
        if flood_type in [4, 5] and value != "0":
            mode += f" for {value}"
        return await message.reply(f"Current antiflood punishment mode is: <b>{mode}</b>")
        
    parts = args.lower().split()
    mode = parts[0]
    
    time_val = "0"
    if mode in ["tban", "tempban", "tmute", "tempmute"]:
        if len(parts) < 2:
            return await message.reply(f"Please specify a time duration for {mode} (e.g. <code>/setfloodmode {mode} 1h</code>).")
        time_val = parts[1]
        
    mode_map = {"ban": 1, "kick": 2, "mute": 3, "tban": 4, "tempban": 4, "tmute": 5, "tempmute": 5}
    if mode not in mode_map:
        return await message.reply("Unknown mode! Available modes: ban, kick, mute, tban, tmute.")
        
    await sql.set_flood_strength(message.chat.id, mode_map[mode], time_val)
    msg = f"Antiflood punishment has been set to <b>{mode}</b>"
    if time_val != "0":
        msg += f" for <b>{time_val}</b>"
    await message.reply(msg + ".")


@antiflood_router.message(F.chat.type.in_({"group", "supergroup"}))
async def flood_watcher(message: Message, bot: Bot):
    user = message.from_user
    chat = message.chat
    
    if not user:
        raise SkipHandler()
        
    limit = await sql.get_flood_limit(chat.id)
    if limit == 0:
        raise SkipHandler()
        
    # Check if flood limit is exceeded
    should_punish = await sql.update_flood(chat.id, user.id)
    if not should_punish:
        raise SkipHandler()
        
    # Ignore admins/bot
    try:
        member = await bot.get_chat_member(chat.id, user.id)
        if member.status in ["creator", "administrator"]:
            raise SkipHandler()
    except Exception:
        pass
        
    if user.id == bot.id:
        raise SkipHandler()
        
    flood_type, value = await sql.get_flood_setting(chat.id)
    name = f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"
    
    try:
        if flood_type == 1:  # ban
            await bot.ban_chat_member(chat.id, user.id)
            await message.answer(f"{html.escape(name)} has been banned for flooding more than {limit} messages in a row!")
            
        elif flood_type == 2:  # kick
            await bot.ban_chat_member(chat.id, user.id)
            await bot.unban_chat_member(chat.id, user.id)
            await message.answer(f"{html.escape(name)} has been kicked for flooding!")
            
        elif flood_type == 3:  # mute
            await bot.restrict_chat_member(chat.id, user.id, permissions=ChatPermissions(can_send_messages=False))
            await message.answer(f"{html.escape(name)} has been muted for flooding!")
            
        elif flood_type == 4:  # tban
            until_date = extract_time(value)
            if not until_date:
                until_date = extract_time("1d")  # Fallback to 1 day
            await bot.ban_chat_member(chat.id, user.id, until_date=until_date)
            await message.answer(f"{html.escape(name)} has been temporarily banned for flooding!")
            
        elif flood_type == 5:  # tmute
            until_date = extract_time(value)
            if not until_date:
                until_date = extract_time("1d")
            await bot.restrict_chat_member(chat.id, user.id, permissions=ChatPermissions(can_send_messages=False), until_date=until_date)
            await message.answer(f"{html.escape(name)} has been temporarily muted for flooding!")
            
    except TelegramBadRequest as e:
        if "not enough rights" in str(e).lower():
            await message.answer(f"I tried to punish {html.escape(name)} for flooding, but I don't have enough admin rights to restrict members!")

    raise SkipHandler()

__help__ = """
<b>Admin Commands:</b>
- <code>/setflood [amount]</code>: Set the maximum number of consecutive messages a user can send before being punished. Set to 0 to disable.
- <code>/setfloodmode [ban/kick/mute/tban/tmute] [time]</code>: Set the action to take when a user exceeds the flood limit. Time is required for tban/tmute (e.g., <code>1h</code>).
"""

register_help("Anti-Flood", __help__)
