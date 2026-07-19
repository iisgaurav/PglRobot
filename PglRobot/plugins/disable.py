# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: @VegaCodesHQ (vegacodes.com)
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from PglRobot.database import disable_sql as sql
from PglRobot.utils.admin_filters import IsAdmin
from PglRobot.utils.help_system import register_help

disable_router = Router()

ADMIN_OR_OWNER = IsAdmin("can_change_info")

# These commands cannot be disabled to prevent soft-locking the bot
NON_DISABLEABLE = ["enable", "disable", "disabled", "help", "start"]

@disable_router.message(
    Command("disable"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER
)
async def disable_cmd(message: Message, command: CommandObject):
    args = command.args
    if not args:
        return await message.reply("Please specify a command to disable (e.g., <code>/disable karma</code>).")
        
    cmd_to_disable = args.split()[0].lower().strip("/")
    
    if cmd_to_disable in NON_DISABLEABLE:
        return await message.reply(f"You cannot disable the <code>{cmd_to_disable}</code> command!")
        
    success = await sql.disable_command(message.chat.id, cmd_to_disable)
    if success:
        await message.reply(f"✅ The <code>{cmd_to_disable}</code> command has been disabled in this chat.\nNormal users will no longer be able to use it.")
    else:
        await message.reply(f"The <code>{cmd_to_disable}</code> command is already disabled!")


@disable_router.message(
    Command("enable"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER
)
async def enable_cmd(message: Message, command: CommandObject):
    args = command.args
    if not args:
        return await message.reply("Please specify a command to enable (e.g., <code>/enable karma</code>).")
        
    cmd_to_enable = args.split()[0].lower().strip("/")
    
    success = await sql.enable_command(message.chat.id, cmd_to_enable)
    if success:
        await message.reply(f"✅ The <code>{cmd_to_enable}</code> command has been enabled in this chat.")
    else:
        await message.reply(f"The <code>{cmd_to_enable}</code> command is not disabled!")


@disable_router.message(
    Command("disabled"),
    F.chat.type.in_({"group", "supergroup"}),
    ADMIN_OR_OWNER
)
async def list_disabled(message: Message):
    disabled_cmds = await sql.get_all_disabled(message.chat.id)
    if not disabled_cmds:
        return await message.reply("There are no disabled commands in this chat.")
        
    text = "🚫 <b>Disabled Commands in this Chat:</b>\n"
    for cmd in sorted(disabled_cmds):
        text += f" - <code>{cmd}</code>\n"
        
    text += "\nUse <code>/enable <command></code> to re-enable them."
    await message.reply(text)


__help__ = """
<b>Admin Commands:</b>
- <code>/disable [command]</code>: Disables a specific bot command in your group.
- <code>/enable [command]</code>: Re-enables a disabled command.
- <code>/disabled</code>: Lists all disabled commands in the current group.

*Note: You do not need to include the slash when disabling (e.g. <code>/disable rules</code> and <code>/disable /rules</code> both work).*
"""

register_help("Disabling", __help__)
