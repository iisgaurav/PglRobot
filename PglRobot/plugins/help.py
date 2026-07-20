# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.deep_linking import create_start_link

from PglRobot.utils.help_system import get_all_modules, get_help

help_router = Router()

class HelpCallback(CallbackData, prefix="help"):
    action: str
    module: str = ""
    page: int = 0

def get_help_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    modules = get_all_modules()
    
    # Pagination: 10 modules per page (2 columns, 5 rows)
    PER_PAGE = 10
    start_idx = page * PER_PAGE
    end_idx = start_idx + PER_PAGE

    current_modules = modules[start_idx:end_idx]

    keyboard = []
    row = []
    for i, mod in enumerate(current_modules):
        # Include current page in callback data to allow returning to same page
        row.append(InlineKeyboardButton(text=mod, callback_data=HelpCallback(action="module", module=mod, page=page).pack()))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Add navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=HelpCallback(action="page", page=page-1).pack()))
    if end_idx < len(modules):
        nav_row.append(InlineKeyboardButton(text="Next ➡️", callback_data=HelpCallback(action="page", page=page+1).pack()))

    if nav_row:
        keyboard.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

HELP_STRINGS = """
Hi! I'm <b>PglRobot</b>. ⚡️

I'm your all-in-one toolkit for leveling up your community. From cutting-edge moderation to gamified reputation systems, I've got you covered.

<i>Developed by @iisgaurav</i>

Choose a module below to see its commands!
"""

@help_router.message(Command("help"), F.chat.type.in_({"group", "supergroup"}))
async def help_group(message: Message, bot: Bot):
    link = await create_start_link(bot, "help", encode=False)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Help", url=link)]
    ])
    await message.reply("Contact me in PM to get the list of possible commands.", reply_markup=keyboard)

@help_router.message(Command("help"), F.chat.type == "private")
async def help_pm(message: Message):
    await message.reply(HELP_STRINGS, reply_markup=get_help_keyboard(0), parse_mode="HTML")

@help_router.message(CommandStart(deep_link=True))
async def start_help_pm(message: Message, command: CommandObject):
    payload = command.args
    if payload == "help":
        await message.reply(HELP_STRINGS, reply_markup=get_help_keyboard(0), parse_mode="HTML")

@help_router.callback_query(HelpCallback.filter(F.action == "page"))
async def help_page_callback(query: CallbackQuery, callback_data: HelpCallback):
    if isinstance(query.message, Message):
        await query.message.edit_text(HELP_STRINGS, reply_markup=get_help_keyboard(callback_data.page), parse_mode="HTML")
    await query.answer()

ALLOWED_TAGS = {"b", "strong", "i", "em", "code", "s", "strike", "del", "u", "ins", "pre"}

def sanitize_html(text: str) -> str:
    def replacer(match):
        tag = match.group(1).lower()
        if tag.startswith("a "):
            return match.group(0)
        clean_tag = tag.replace("/", "")
        if clean_tag in ALLOWED_TAGS or clean_tag == "a":
            return match.group(0)
        return f"&lt;{match.group(1)}&gt;"
    return re.sub(r'<([^>]+)>', replacer, text)

@help_router.callback_query(HelpCallback.filter(F.action == "module"))
async def help_module_callback(query: CallbackQuery, callback_data: HelpCallback):
    mod = callback_data.module
    text = f"Here is the help for the <b>{mod}</b> module:\n\n{sanitize_html(get_help(mod))}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back", callback_data=HelpCallback(action="page", page=callback_data.page).pack())]
    ])
    
    if isinstance(query.message, Message):
        try:
            await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise
    await query.answer()
