# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject

from PglRobot.utils.admin_filters import IsAdmin, BotCan
from PglRobot.utils.extraction import extract_user_and_reason
from PglRobot.utils.time_parser import extract_time

muting_router = Router()

ADMIN_OR_OWNER = IsAdmin("can_restrict_members")
BOT_CAN_RESTRICT = BotCan("can_restrict_members")

@muting_router.message(Command("mute", "m", "unmute", "tmute", "tempmute"), F.chat.type == "private")
async def pm_fallback(message: Message):
    await message.reply("This command can only be used in groups.")


@muting_router.message(Command("mute", "m"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER, BOT_CAN_RESTRICT)
async def mute_user(message: Message, command: CommandObject):
    user_id, reason = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to mute.")
        
    if user_id == message.bot.id:
        return await message.reply("I can't mute myself!")
        
    from PglRobot.utils.admin_filters import check_if_admin
    if await check_if_admin(message.chat, user_id):
        return await message.reply("I'm not going to mute an admin!")
        
    try:
        perms = ChatPermissions(can_send_messages=False)
        await message.bot.restrict_chat_member(chat_id=message.chat.id, user_id=user_id, permissions=perms)
        text = f"Muted user {user_id} permanently."
        if reason:
            text += f"\nReason: {reason}"
        await message.reply(text)
    except Exception as e:
        await message.reply(f"Failed to mute user. Error: {str(e)}")


@muting_router.message(Command("unmute"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER, BOT_CAN_RESTRICT)
async def unmute_user(message: Message, command: CommandObject):
    user_id, reason = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to unmute.")
        
    try:
        perms = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        await message.bot.restrict_chat_member(chat_id=message.chat.id, user_id=user_id, permissions=perms)
        text = f"Unmuted user {user_id}."
        if reason:
            text += f"\nReason: {reason}"
        await message.reply(text)
    except Exception as e:
        await message.reply(f"Failed to unmute user. Error: {str(e)}")


@muting_router.message(Command("tmute", "tempmute"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER, BOT_CAN_RESTRICT)
async def temp_mute_user(message: Message, command: CommandObject):
    # args: <user> <time> <reason>
    # if replied, args: <time> <reason>
    if not command.args:
        return await message.reply("Specify a user and time to mute (e.g. 1d).")

    args = command.args.split()
    user_id = None
    time_val = None
    reason_start = 0

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        time_val = args[0]
        reason_start = 1
    else:
        if len(args) < 2:
            return await message.reply("Specify a user and time to mute (e.g. 1d).")
        try:
            user_id = int(args[0])
        except ValueError:
            # We assume it's a mention or something else, but for simplicity we need numeric IDs or relies
            if message.entities:
                for entity in message.entities:
                    if entity.type == "text_mention" and entity.user:
                        user_id = entity.user.id
                        break
        time_val = args[1]
        reason_start = 2

    if not user_id:
        return await message.reply("Could not extract user ID.")

    if user_id == message.bot.id:
        return await message.reply("I can't mute myself!")

    from PglRobot.utils.admin_filters import check_if_admin
    if await check_if_admin(message.chat, user_id):
        return await message.reply("I'm not going to mute an admin!")

    mutetime = extract_time(time_val)
    if not mutetime:
        return await message.reply("Invalid time format. Use something like 10m, 1h, or 1d.")

    reason = " ".join(args[reason_start:]) if len(args) > reason_start else ""

    try:
        perms = ChatPermissions(can_send_messages=False)
        await message.bot.restrict_chat_member(
            chat_id=message.chat.id, 
            user_id=user_id, 
            permissions=perms,
            until_date=mutetime
        )
        text = f"Muted user {user_id} for {time_val}."
        if reason:
            text += f"\nReason: {reason}"
        await message.reply(text)
    except Exception as e:
        await message.reply(f"Failed to temp-mute user. Error: {str(e)}")

__help__ = """
<b>Muting Commands:</b>
- <code>/mute</code> or <code>/m</code>: Mutes a user permanently.
- <code>/unmute</code>: Unmutes a user.
- <code>/tmute <time></code> or <code>/tempmute <time></code>: Temporarily mutes a user.
Time format examples: <code>1d</code> (1 day), <code>2h</code> (2 hours), <code>30m</code> (30 minutes).
"""
from PglRobot.utils.help_system import register_help
register_help("Muting", __help__)
