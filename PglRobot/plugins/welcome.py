# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import logging
import re
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode, ChatMemberStatus

from PglRobot.utils.admin_filters import IsAdmin
from PglRobot.database import welcome_sql as sql
from PglRobot.utils.help_system import register_help

logger = logging.getLogger(__name__)

welcome_router = Router()
ADMIN = IsAdmin("can_change_info")

def parse_buttons(text: str) -> tuple[str, InlineKeyboardMarkup | None]:
    if not text:
        return text, None
        
    buttons = []
    clean_text = text
    
    for match in re.finditer(r"\[([^\[\]]+)\]\(buttonurl:(.*?)\)", text, re.IGNORECASE):
        btn_text = match.group(1)
        btn_url = match.group(2).strip()
        buttons.append(InlineKeyboardButton(text=btn_text, url=btn_url))
        clean_text = clean_text.replace(match.group(0), "")
        
    if not buttons:
        return clean_text.strip(), None
        
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn] for btn in buttons])
    return clean_text.strip(), kb

def format_text(text: str, user, chat_title: str) -> str:
    if not text:
        return text
    first = user.first_name or ""
    last = user.last_name or ""
    fullname = f"{first} {last}".strip()
    username = f"@{user.username}" if user.username else fullname
    mention = f"<a href='tg://user?id={user.id}'>{first}</a>"
    
    text = text.replace("{first}", first)
    text = text.replace("{last}", last)
    text = text.replace("{fullname}", fullname)
    text = text.replace("{username}", username)
    text = text.replace("{id}", str(user.id))
    text = text.replace("{chatname}", chat_title)
    text = text.replace("{mention}", mention)
    return text


@welcome_router.chat_member()
async def welcome_goodbye_handler(event: ChatMemberUpdated, bot: Bot):
    chat = event.chat
    if chat.type == "private":
        return

    old = event.old_chat_member
    new = event.new_chat_member
    user = new.user

    # Handle Welcome
    if old.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED) and new.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED):
        pref = await sql.get_welcome_pref(chat.id)
        if not pref["should_welcome"]:
            return
            
        raw_text = pref["welcome_text"] or sql.get_random_welcome()
        text = format_text(raw_text, user, chat.title or "")
        text, kb = parse_buttons(text)
        
        # Clean previous welcome if enabled
        if pref["clean_welcome"] and pref["last_welcome_msg_id"]:
            try:
                await bot.delete_message(chat.id, pref["last_welcome_msg_id"])
            except Exception:
                pass
                
        sent_msg = None
        try:
            if not pref["welcome_media_id"]:
                sent_msg = await bot.send_message(chat.id, text, reply_markup=kb, parse_mode=ParseMode.HTML)
            else:
                m_type = pref["welcome_media_type"]
                m_id = pref["welcome_media_id"]
                if m_type == 1:
                    sent_msg = await bot.send_photo(chat.id, m_id, caption=text, reply_markup=kb, parse_mode=ParseMode.HTML)
                elif m_type == 2:
                    sent_msg = await bot.send_video(chat.id, m_id, caption=text, reply_markup=kb, parse_mode=ParseMode.HTML)
                elif m_type == 3:
                    sent_msg = await bot.send_animation(chat.id, m_id, caption=text, reply_markup=kb, parse_mode=ParseMode.HTML)
                else:
                    sent_msg = await bot.send_message(chat.id, text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
            
        if sent_msg and pref["clean_welcome"]:
            await sql.set_last_welcome_msg_id(chat.id, sent_msg.message_id)

    # Handle Goodbye
    elif old.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED, ChatMemberStatus.ADMINISTRATOR) and new.status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
        pref = await sql.get_welcome_pref(chat.id)
        if not pref["should_goodbye"]:
            return
            
        raw_text = pref["leave_text"] or sql.get_random_goodbye()
        text = format_text(raw_text, user, chat.title or "")
        text, kb = parse_buttons(text)
        
        sent_msg = None
        try:
            if not pref["leave_media_id"]:
                sent_msg = await bot.send_message(chat.id, text, reply_markup=kb, parse_mode=ParseMode.HTML)
            else:
                m_type = pref["leave_media_type"]
                m_id = pref["leave_media_id"]
                if m_type == 1:
                    sent_msg = await bot.send_photo(chat.id, m_id, caption=text, reply_markup=kb, parse_mode=ParseMode.HTML)
                elif m_type == 2:
                    sent_msg = await bot.send_video(chat.id, m_id, caption=text, reply_markup=kb, parse_mode=ParseMode.HTML)
                elif m_type == 3:
                    sent_msg = await bot.send_animation(chat.id, m_id, caption=text, reply_markup=kb, parse_mode=ParseMode.HTML)
                else:
                    sent_msg = await bot.send_message(chat.id, text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to send goodbye message: {e}")


# Commands
@welcome_router.message(Command("welcome"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def welcome_toggle(message: Message, command: CommandObject):
    args = command.args.lower() if command.args else ""
    if args in ("on", "yes", "true"):
        await sql.set_welcome_status(message.chat.id, True)
        await message.reply("✅ Welcome messages are now <b>enabled</b>.", parse_mode=ParseMode.MARKDOWN)
    elif args in ("off", "no", "false"):
        await sql.set_welcome_status(message.chat.id, False)
        await message.reply("❌ Welcome messages are now <b>disabled</b>.", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("Usage: <code>/welcome on</code> or <code>/welcome off</code>", parse_mode=ParseMode.MARKDOWN)

@welcome_router.message(Command("goodbye"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def goodbye_toggle(message: Message, command: CommandObject):
    args = command.args.lower() if command.args else ""
    if args in ("on", "yes", "true"):
        await sql.set_goodbye_status(message.chat.id, True)
        await message.reply("✅ Goodbye messages are now <b>enabled</b>.", parse_mode=ParseMode.MARKDOWN)
    elif args in ("off", "no", "false"):
        await sql.set_goodbye_status(message.chat.id, False)
        await message.reply("❌ Goodbye messages are now <b>disabled</b>.", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("Usage: <code>/goodbye on</code> or <code>/goodbye off</code>", parse_mode=ParseMode.MARKDOWN)

@welcome_router.message(Command("cleanwelcome"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def cleanwelcome_toggle(message: Message, command: CommandObject):
    args = command.args.lower() if command.args else ""
    if args in ("on", "yes", "true"):
        await sql.set_clean_welcome(message.chat.id, True)
        await message.reply("✅ Clean welcome is now <b>enabled</b>. I will delete the old welcome message when a new one is sent.", parse_mode=ParseMode.MARKDOWN)
    elif args in ("off", "no", "false"):
        await sql.set_clean_welcome(message.chat.id, False)
        await message.reply("❌ Clean welcome is now <b>disabled</b>.", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("Usage: <code>/cleanwelcome on</code> or <code>/cleanwelcome off</code>", parse_mode=ParseMode.MARKDOWN)

@welcome_router.message(Command("setwelcome"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def set_welcome(message: Message, command: CommandObject):
    text = command.args
    reply = message.reply_to_message
    
    media_id = None
    media_type = 0
    
    if reply:
        if reply.photo:
            media_id = reply.photo[-1].file_id
            media_type = 1
        elif reply.video:
            media_id = reply.video.file_id
            media_type = 2
        elif reply.animation:
            media_id = reply.animation.file_id
            media_type = 3
            
        if not text:
            text = reply.caption or reply.text
            
    if not text and not media_id:
        return await message.reply("You need to provide text or reply to a message/media to set it as the welcome message.")
        
    await sql.set_welcome_message(message.chat.id, text, media_id, media_type)
    await message.reply("✅ Custom welcome message saved!")

@welcome_router.message(Command("setgoodbye"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def set_goodbye(message: Message, command: CommandObject):
    text = command.args
    reply = message.reply_to_message
    
    media_id = None
    media_type = 0
    
    if reply:
        if reply.photo:
            media_id = reply.photo[-1].file_id
            media_type = 1
        elif reply.video:
            media_id = reply.video.file_id
            media_type = 2
        elif reply.animation:
            media_id = reply.animation.file_id
            media_type = 3
            
        if not text:
            text = reply.caption or reply.text
            
    if not text and not media_id:
        return await message.reply("You need to provide text or reply to a message/media to set it as the goodbye message.")
        
    await sql.set_goodbye_message(message.chat.id, text, media_id, media_type)
    await message.reply("✅ Custom goodbye message saved!")

@welcome_router.message(Command("resetwelcome"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def reset_welcome(message: Message):
    await sql.set_welcome_message(message.chat.id, None, None, 0)
    await message.reply("✅ Welcome message has been reset to default.")

@welcome_router.message(Command("resetgoodbye"), F.chat.type.in_({"group", "supergroup"}), ADMIN)
async def reset_goodbye(message: Message):
    await sql.set_goodbye_message(message.chat.id, None, None, 0)
    await message.reply("✅ Goodbye message has been reset to default.")


__help__ = """
<b>👋 Welcome & Goodbye</b>

Control how the bot greets and says goodbye to users.

<b>Admin Commands:</b>
• /welcome <code><on/off></code> — Enable or disable welcome messages.
• /goodbye <code><on/off></code> — Enable or disable goodbye messages.
• /cleanwelcome <code><on/off></code> — Delete the old welcome message when a new one is sent.
• /setwelcome <code><text/reply></code> — Set a custom welcome message. You can reply to a photo, video, or gif!
• /setgoodbye <code><text/reply></code> — Set a custom goodbye message.
• /resetwelcome — Reset welcome message to default.
• /resetgoodbye — Reset goodbye message to default.

<b>Formatting Tags:</b>
You can use these tags in your custom messages:
• <code>{first}</code> - User's first name
• <code>{last}</code> - User's last name
• <code>{fullname}</code> - User's full name
• <code>{username}</code> - User's username
• <code>{mention}</code> - Mentions the user
• <code>{id}</code> - User's ID
• <code>{chatname}</code> - The group's name

<b>Buttons:</b>
You can add buttons by using this format:
<code>[Button Text](buttonurl:https://google.com)</code>
"""

register_help("Welcome", __help__)
