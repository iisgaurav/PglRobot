# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: @VegaCodesHQ (vegacodes.com)
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject

from PglRobot.utils.admin_filters import IsAdmin, BotCan
from PglRobot.utils.extraction import extract_user_and_reason

bans_router = Router()

# Shared filters for restriction commands
ADMIN_OR_OWNER = IsAdmin("can_restrict_members")
BOT_CAN_RESTRICT = BotCan("can_restrict_members")

@bans_router.message(Command("ban", "b", "unban", "kick", "k", "mute", "m", "unmute"), F.chat.type == "private")
async def pm_fallback(message: Message):
    await message.reply("This command can only be used in groups.")


@bans_router.message(Command("ban", "b"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER, BOT_CAN_RESTRICT)
async def ban_user(message: Message, command: CommandObject):
    user_id, reason = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("I don't know who you're talking about, you're going to need to specify a user.")
    
    if user_id == message.bot.id:
        return await message.reply("I'm not going to ban myself!")
        
    from PglRobot.utils.admin_filters import check_if_admin
    if await check_if_admin(message.chat, user_id):
        return await message.reply("I'm not going to ban an admin!")
        
    try:
        await message.bot.ban_chat_member(chat_id=message.chat.id, user_id=user_id)
        text = f"Banned user {user_id}."
        if reason:
            text += f"\nReason: {reason}"
        await message.reply(text)
    except Exception as e:
        await message.reply(f"Failed to ban user. Error: {str(e)}")


@bans_router.message(Command("unban"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER, BOT_CAN_RESTRICT)
async def unban_user(message: Message, command: CommandObject):
    user_id, reason = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to unban.")
        
    try:
        await message.bot.unban_chat_member(chat_id=message.chat.id, user_id=user_id, only_if_banned=True)
        text = f"Unbanned user {user_id}."
        if reason:
            text += f"\nReason: {reason}"
        await message.reply(text)
    except Exception as e:
        await message.reply(f"Failed to unban user. Error: {str(e)}")


@bans_router.message(Command("kick", "k"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER, BOT_CAN_RESTRICT)
async def kick_user(message: Message, command: CommandObject):
    user_id, reason = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to kick.")
        
    if user_id == message.bot.id:
        return await message.reply("I'm not going to kick myself!")
        
    from PglRobot.utils.admin_filters import check_if_admin
    if await check_if_admin(message.chat, user_id):
        return await message.reply("I'm not going to kick an admin!")
        
    try:
        # Kicking in Telegram is just unbanning a user which removes them without keeping them banned.
        await message.bot.ban_chat_member(chat_id=message.chat.id, user_id=user_id)
        await message.bot.unban_chat_member(chat_id=message.chat.id, user_id=user_id)
        text = f"Kicked user {user_id}."
        if reason:
            text += f"\nReason: {reason}"
        await message.reply(text)
    except Exception as e:
        await message.reply(f"Failed to kick user. Error: {str(e)}")


@bans_router.message(Command("mute", "m"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER, BOT_CAN_RESTRICT)
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
        text = f"Muted user {user_id}."
        if reason:
            text += f"\nReason: {reason}"
        await message.reply(text)
    except Exception as e:
        await message.reply(f"Failed to mute user. Error: {str(e)}")


@bans_router.message(Command("unmute"), F.chat.type.in_({"group", "supergroup"}), ADMIN_OR_OWNER, BOT_CAN_RESTRICT)
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

__help__ = """
*Bans Commands:*
 • <code>/ban</code> or <code>/b</code>: Bans a user from the chat.
 • <code>/unban</code>: Unbans a user.
 • <code>/kick</code> or <code>/k</code>: Kicks a user.
 • <code>/mute</code> or <code>/m</code>: Mutes a user.
 • <code>/unmute</code>: Unmutes a user.

Note: You can optionally specify a reason like <code>/ban @user being a jerk</code>
"""
from PglRobot.utils.help_system import register_help
register_help("Bans", __help__)
