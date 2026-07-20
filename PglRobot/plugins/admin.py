# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import html
from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ChatPermissions
from aiogram.exceptions import TelegramBadRequest

from PglRobot.utils.admin_filters import IsAdmin, BotCan, check_if_admin
from PglRobot.utils.extraction import extract_user_and_reason
from PglRobot.utils.time_parser import extract_time
from PglRobot.database import warns_sql as sql

router = Router()

ADMIN_OR_OWNER = IsAdmin("can_restrict_members")
BOT_CAN_RESTRICT = BotCan("can_restrict_members")

# ============================================================
# PM Fallback — all group-only commands in one handler
# ============================================================

@router.message(
    Command(
        "ban", "dban", "unban", "kick",
        "mute", "m", "unmute",
        "tmute", "tempmute",
        "warn", "unwarn", "rmwarn", "warns", "warnlimit",
        "pin", "unpin",
    ),
    F.chat.type == "private",
)
async def group_only_pm(message: Message):
    await message.reply("This command can only be used in groups.")


# ============================================================
# BAN / UNBAN
# ============================================================

@router.message(
    Command("ban", "dban"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
    BOT_CAN_RESTRICT,
)
async def ban_user(message: Message, bot: Bot, command: CommandObject):
    user_id, reason = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("I don't know who you're talking about, you're going to need to specify a user.")

    if user_id == bot.id:
        return await message.reply("I'm not going to ban myself, are you crazy?")

    if await check_if_admin(message.chat, user_id):
        return await message.reply("I'm not going to ban an admin!")

    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        reply = "Banned!"
        if reason:
            reply += f"\nReason: {html.escape(reason or '')}"
        await message.reply(reply)
    except TelegramBadRequest as e:
        await message.reply(f"Failed to ban: {e}")


@router.message(
    Command("unban"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
    BOT_CAN_RESTRICT,
)
async def unban_user(message: Message, bot: Bot, command: CommandObject):
    user_id, _ = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to unban.")

    try:
        await bot.unban_chat_member(message.chat.id, user_id, only_if_banned=True)
        await message.reply("Unbanned!")
    except TelegramBadRequest:
        await message.reply("I can't unban that user.")


# ============================================================
# KICK
# ============================================================

@router.message(
    Command("kick", "k"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
    BOT_CAN_RESTRICT,
)
async def kick_user(message: Message, bot: Bot, command: CommandObject):
    user_id, reason = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to kick.")

    if user_id == bot.id:
        return await message.reply("I'm not going to kick myself!")

    if await check_if_admin(message.chat, user_id):
        return await message.reply("I'm not going to kick an admin!")

    try:
        await bot.ban_chat_member(message.chat.id, user_id)
        await bot.unban_chat_member(message.chat.id, user_id)
        reply = "Kicked!"
        if reason:
            reply += f"\nReason: {html.escape(reason or '')}"
        await message.reply(reply)
    except TelegramBadRequest:
        await message.reply("I can't kick that user.")


# ============================================================
# MUTE / UNMUTE / TEMPMUTE
# ============================================================

@router.message(
    Command("mute", "m"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
    BOT_CAN_RESTRICT,
)
async def mute_user(message: Message, bot: Bot, command: CommandObject):
    user_id, reason = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to mute.")

    if user_id == bot.id:
        return await message.reply("I can't mute myself!")

    if await check_if_admin(message.chat, user_id):
        return await message.reply("I'm not going to mute an admin!")

    try:
        permissions = ChatPermissions(can_send_messages=False)
        await bot.restrict_chat_member(message.chat.id, user_id, permissions=permissions)
        reply = "Muted!"
        if reason:
            reply += f"\nReason: {html.escape(reason or '')}"
        await message.reply(reply)
    except TelegramBadRequest:
        await message.reply("I can't mute that user.")


@router.message(
    Command("unmute"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
    BOT_CAN_RESTRICT,
)
async def unmute_user(message: Message, bot: Bot, command: CommandObject):
    user_id, _ = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to unmute.")

    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        )
        await bot.restrict_chat_member(message.chat.id, user_id, permissions=permissions)
        await message.reply("Unmuted!")
    except TelegramBadRequest:
        await message.reply("I can't unmute that user.")


@router.message(
    Command("tmute", "tempmute"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
    BOT_CAN_RESTRICT,
)
async def temp_mute_user(message: Message, bot: Bot, command: CommandObject):
    if not command.args:
        return await message.reply("Specify a user and time to mute (e.g. /tmute @user 1h reason).")

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
            return await message.reply("Specify a user and time to mute (e.g. /tmute @user 1h reason).")
        try:
            user_id = int(args[0])
        except ValueError:
            if message.entities:
                for entity in message.entities:
                    if entity.type == "text_mention" and entity.user:
                        user_id = entity.user.id
                        break
        time_val = args[1]
        reason_start = 2

    if not user_id:
        return await message.reply("Could not find the user. Reply to their message or provide their ID.")

    if user_id == bot.id:
        return await message.reply("I can't mute myself!")

    if await check_if_admin(message.chat, user_id):
        return await message.reply("I'm not going to mute an admin!")

    mutetime = extract_time(time_val)
    if not mutetime:
        return await message.reply("Invalid time format. Use something like 10m, 1h, or 1d.")

    reason = " ".join(args[reason_start:]) if len(args) > reason_start else ""

    try:
        perms = ChatPermissions(can_send_messages=False)
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=user_id,
            permissions=perms,
            until_date=mutetime,
        )
        reply = f"Muted for {time_val}!"
        if reason:
            reply += f"\nReason: {html.escape(reason or '')}"
        await message.reply(reply)
    except Exception as e:
        await message.reply(f"Failed to temp-mute user. Error: {str(e)}")


# ============================================================
# WARN / UNWARN / WARNS / WARNLIMIT
# ============================================================

@router.message(
    Command("warn"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
    BOT_CAN_RESTRICT,
)
async def warn_user(message: Message, bot: Bot, command: CommandObject):
    user_id, reason = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to warn.")

    if user_id == bot.id:
        return await message.reply("I can't warn myself!")

    if await check_if_admin(message.chat, user_id):
        return await message.reply("I'm not going to warn an admin!")

    chat_id = message.chat.id
    limit, soft_warn = await sql.get_warn_setting(chat_id)
    num_warns, _ = await sql.warn_user(user_id, chat_id, reason)

    if num_warns >= limit:
        await sql.reset_warns(user_id, chat_id)
        if soft_warn:
            try:
                await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
                await message.reply(f"User reached {limit} warns and has been kicked!")
            except Exception as e:
                await message.reply(f"User reached warn limit, but I failed to kick them: {e}")
        else:
            try:
                await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                await message.reply(f"User reached {limit} warns and has been banned!")
            except Exception as e:
                await message.reply(f"User reached warn limit, but I failed to ban them: {e}")
    else:
        text = f"User has been warned. ({num_warns}/{limit})"
        if reason:
            text += f"\nReason: {html.escape(reason or '')}"
        await message.reply(text)


@router.message(
    Command("unwarn", "rmwarn"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
)
async def unwarn_user(message: Message, command: CommandObject):
    user_id, _ = extract_user_and_reason(message, command.args)
    if not user_id:
        return await message.reply("Specify a user to unwarn.")

    removed = await sql.remove_warn(user_id, message.chat.id)
    if removed:
        await message.reply(f"Removed latest warn for that user.")
    else:
        await message.reply("That user has no warns.")


@router.message(
    Command("warns"),
    F.chat.type.in_({"group", "supergroup"}),
)
async def get_user_warns(message: Message, command: CommandObject):
    user_id, _ = extract_user_and_reason(message, command.args)
    if not user_id:
        user_id = message.from_user.id

    warns_data = await sql.get_warns(user_id, message.chat.id)
    if not warns_data or warns_data[0] == 0:
        return await message.reply("That user has no warns!")

    num, reasons = warns_data
    limit, _ = await sql.get_warn_setting(message.chat.id)

    text = f"User has {num}/{limit} warns.\n"
    if reasons:
        text += "Reasons:\n"
        for i, r in enumerate(reasons, 1):
            text += f"{i}. {html.escape(r or '')}\n"
    await message.reply(text)


@router.message(
    Command("warnlimit"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER,
)
async def set_warn_limit(message: Message, command: CommandObject):
    if not command.args:
        limit, _ = await sql.get_warn_setting(message.chat.id)
        return await message.reply(f"Current warn limit is {limit}.")

    try:
        new_limit = int(command.args.split()[0])
        if new_limit < 1:
            return await message.reply("Warn limit must be at least 1.")
        await sql.set_warn_limit(message.chat.id, new_limit)
        await message.reply(f"Warn limit updated to {new_limit}.")
    except ValueError:
        await message.reply("Please provide a valid number.")


# ============================================================
# PIN / UNPIN
# ============================================================

@router.message(
    Command("pin"),
    F.chat.type.in_({"group", "supergroup"}),
    IsAdmin("can_pin_messages"),
)
async def pin_message(message: Message, bot: Bot):
    if not message.reply_to_message:
        return await message.reply("Reply to a message to pin it.")
    try:
        await bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        await message.reply("Pinned!")
    except TelegramBadRequest:
        await message.reply("I can't pin messages here.")


@router.message(
    Command("unpin"),
    F.chat.type.in_({"group", "supergroup"}),
    IsAdmin("can_pin_messages"),
)
async def unpin_message(message: Message, bot: Bot):
    try:
        if message.reply_to_message:
            await bot.unpin_chat_message(message.chat.id, message_id=message.reply_to_message.message_id)
        else:
            await bot.unpin_chat_message(message.chat.id)
        await message.reply("Unpinned!")
    except TelegramBadRequest:
        await message.reply("I can't unpin messages here.")


# ============================================================
# Help
# ============================================================

__help__ = """
<b>🛡️ Admin Commands:</b>

<b>Bans</b>
- <code>/ban</code> or <code>/dban <user></code> — Permanently ban a user.
- <code>/unban <user></code> — Unban a user.
- <code>/kick</code> or <code>/k <user></code> — Kick a user (they can rejoin).

<b>Muting</b>
- <code>/mute</code> or <code>/m <user></code> — Mute a user permanently.
- <code>/unmute <user></code> — Unmute a user.
- <code>/tmute</code> or <code>/tempmute <user> <time></code> — Temporarily mute. (e.g. <code>1h</code>, <code>30m</code>, <code>2d</code>)

<b>Warns</b>
- <code>/warn <user></code> — Warn a user. Hits the limit → auto-ban/kick.
- <code>/unwarn</code> or <code>/rmwarn <user></code> — Remove the latest warn.
- <code>/warns <user></code> — Show a user's warn count and reasons.
- <code>/warnlimit <number></code> — Set the warn limit (default: 3).

<b>Other</b>
- <code>/pin</code> — Reply to a message to pin it.
- <code>/unpin</code> — Unpin a message.

<i>Note: Admins can never be banned, kicked, muted, or warned by the bot.</i>
"""

from PglRobot.utils.help_system import register_help
register_help("Admin", __help__)



from aiogram.types import ChatMemberOwner, ChatMemberAdministrator

async def is_admin(message, user_id: int, chat_id: int | None = None) -> bool:
    """Helper to check if a user is an admin, optionally in a specific chat_id."""
    if chat_id is None:
        chat = message.chat
    else:
        try:
            chat = await message.bot.get_chat(chat_id)
        except Exception:
            return False
            
    if chat.type == "private":
        return True
        
    try:
        member = await chat.get_member(user_id)
        return isinstance(member, (ChatMemberOwner, ChatMemberAdministrator))
    except Exception:
        return False
