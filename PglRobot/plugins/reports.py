# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import html
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from PglRobot.database import reporting_sql as sql
from PglRobot.utils.admin_filters import IsAdmin
from PglRobot.utils.help_system import register_help

reports_router = Router()

ADMIN_OR_OWNER = IsAdmin("can_change_info")


@reports_router.message(
    Command("reports", "report"), 
    F.chat.type.in_({"group", "supergroup"}), 
    ADMIN_OR_OWNER
)
async def toggle_reports(message: Message, command: CommandObject):
    if command.command == "report":
        return  # This is handled by the generic text handler below if triggered normally
        
    args = command.args
    if not args:
        status = await sql.chat_should_report(message.chat.id)
        state_str = "enabled" if status else "disabled"
        return await message.reply(f"Reports are currently <b>{state_str}</b> in this chat.\nTo change it, use <code>/reports on</code> or <code>/reports off</code>.")
        
    toggle = args.lower()
    if toggle in ["on", "yes", "true"]:
        await sql.set_chat_setting(message.chat.id, True)
        await message.reply("Reports have been <b>enabled</b> in this chat. Users can now use <code>@admin</code> or <code>/report</code> to notify admins.")
    elif toggle in ["off", "no", "false"]:
        await sql.set_chat_setting(message.chat.id, False)
        await message.reply("Reports have been <b>disabled</b> in this chat.")
    else:
        await message.reply("Invalid argument. Use <code>on</code> or <code>off</code>.")


@reports_router.message(
    F.chat.type.in_({"group", "supergroup"}) & 
    (F.text.startswith("@admin") | F.text.startswith("/report"))
)
async def report_message(message: Message, bot: Bot):
    user = message.from_user
    chat = message.chat
    
    # Check if reports are enabled in this chat
    if not await sql.chat_should_report(chat.id):
        return
        
    # Check if this user is allowed to report
    if not await sql.user_should_report(user.id):
        return
        
    # Must reply to a message to report it
    if not message.reply_to_message:
        await message.reply("Please reply to a message to report it to the admins.")
        return
        
    target_msg = message.reply_to_message
    if target_msg.from_user and target_msg.from_user.id == bot.id:
        await message.reply("Why would you report me? :(")
        return
        
    # Get admins
    try:
        admins = await bot.get_chat_administrators(chat.id)
    except Exception:
        return
        
    admin_tags = []
    for admin in admins:
        if admin.user.is_bot or admin.user.id == user.id:
            continue
        admin_tags.append(f'<a href="tg://user?id={admin.user.id}">\u200b</a>')
        
    if not admin_tags:
        await message.reply("There are no human admins to report to!")
        return
        
    invisible_tags = "".join(admin_tags)
    report_text = f"{invisible_tags}<b>Report!</b>\n<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a> has reported a message to the admins."
    
    await message.reply_to_message.reply(report_text, parse_mode="HTML")


__help__ = """
<b>Admin Commands:</b>
- <code>/reports [on/off]</code>: Enable or disable the reporting feature for your group.

<b>User Commands:</b>
- <code>/report</code> or <code>@admin</code>: Reply to a message to report it to all admins.
"""

register_help("Reports", __help__)
