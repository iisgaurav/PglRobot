# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: @VegaCodesHQ (vegacodes.com)
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import asyncio
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from PglRobot.utils.admin_filters import IsSudoUser
from PglRobot.database import users_sql
from PglRobot.utils.help_system import register_help

broadcast_router = Router()

@broadcast_router.message(Command("broadcast"), IsSudoUser())
async def broadcast_command(message: Message, command: CommandObject):
    args = command.args
    if not args and not message.reply_to_message:
        return await message.reply(
            "<b>Usage:</b> <code>/broadcast &lt;users|groups|all&gt;</code> (reply to a message)\nOr: <code>/broadcast &lt;users|groups|all&gt; &lt;text&gt;</code>",
            parse_mode="HTML"
        )
        
    if args:
        target_str = args.split()[0].lower()
    else:
        target_str = "all"
        
    if target_str not in ["users", "groups", "all"]:
        return await message.reply("Target must be <code>users</code>, <code>groups</code>, or <code>all</code>.", parse_mode="HTML")
        
    targets = []
    if target_str in ["users", "all"]:
        users = await users_sql.get_all_users()
        targets.extend(users)
        
    if target_str in ["groups", "all"]:
        groups = await users_sql.get_all_chats()
        targets.extend([int(g) for g in groups])
        
    if not targets:
        return await message.reply("No targets found to broadcast to!")
        
    status_msg = await message.reply(f"🚀 <b>Broadcast started to {len(targets)} targets...</b>", parse_mode="HTML")
    
    success = 0
    failed = 0
    
    for target in targets:
        try:
            if message.reply_to_message:
                await message.reply_to_message.copy_to(target)
            else:
                text_to_send = args[len(target_str):].strip()
                if not text_to_send:
                    continue
                await message.bot.send_message(target, text_to_send, parse_mode="HTML")
                
            success += 1
            await asyncio.sleep(0.05)  # 20 messages per second limit for broadcasts
        except Exception:
            failed += 1
            
    await status_msg.edit_text(
        f"✅ <b>Broadcast Complete!</b>\n\n🎯 <b>Total Targets:</b> <code>{len(targets)}</code>\n✅ <b>Success:</b> <code>{success}</code>\n❌ <b>Failed:</b> <code>{failed}</code>",
        parse_mode="HTML"
    )

__help__ = """
<b>📢 Broadcast System</b>

<b>Sudo Commands:</b>
- <code>/broadcast &lt;users|groups|all&gt; [text]</code>: Broadcasts a message to tracked users and groups. If used as a reply, it will copy the replied message (including media) to all targets.

<i>Note: Telegram enforces strict flood limits. Broadcasting to thousands of chats will take some time.</i>
"""
register_help("Broadcast", __help__)
