# ==============================================================================
# PglRobot 2.0 - Next Generation Telegram Moderation Engine
# Ecosystem: @TeamAuraX
# Powered By: www.vegacodes.com
# Developer: Gaurav Verma (@iisgaurav)
# ==============================================================================

import platform
import sys
import psutil
import time
import aiogram
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

from PglRobot import StartTime
from PglRobot.utils.admin_filters import IsSudoUser

router = Router()


def fmt_bytes(bytes_val: int | float) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def progress_bar(percent: float, length: int = 10) -> str:
    """Generate a text progress bar."""
    filled = int(length * percent / 100)
    bar = "█" * filled + "░" * (length - filled)
    return bar


def get_readable_time(seconds: int) -> str:
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


@router.message(Command("sysinfo", "deploy"), IsSudoUser())
async def sys_info(message: Message):
    # --- Timing ---
    uptime = get_readable_time(int(time.time() - StartTime))

    # --- CPU ---
    cpu_pct = psutil.cpu_percent(interval=0.5)
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_count_physical = psutil.cpu_count(logical=False)
    try:
        cpu_freq = psutil.cpu_freq()
        freq_str = f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A"
    except Exception:
        freq_str = "N/A"

    # --- RAM ---
    ram = psutil.virtual_memory()
    ram_used = fmt_bytes(ram.used)
    ram_total = fmt_bytes(ram.total)
    ram_avail = fmt_bytes(ram.available)
    ram_pct = ram.percent

    # --- Swap ---
    swap = psutil.swap_memory()
    swap_used = fmt_bytes(swap.used)
    swap_total = fmt_bytes(swap.total)
    swap_pct = swap.percent

    # --- Disk ---
    try:
        disk = psutil.disk_usage("/")
    except Exception:
        disk = psutil.disk_usage("C:\\")
    disk_used = fmt_bytes(disk.used)
    disk_total = fmt_bytes(disk.total)
    disk_free = fmt_bytes(disk.free)
    disk_pct = disk.percent

    # --- Network ---
    net = psutil.net_io_counters()
    net_sent = fmt_bytes(net.bytes_sent)
    net_recv = fmt_bytes(net.bytes_recv)

    # --- Process ---
    proc = psutil.Process()
    bot_mem = fmt_bytes(proc.memory_info().rss)
    bot_threads = proc.num_threads()

    # --- OS ---
    os_name = platform.system()
    os_release = platform.release()
    os_arch = platform.machine()
    hostname = platform.node()
    py_ver = sys.version.split()[0]
    aiogram_ver = aiogram.__version__

    text = (
        f"🖥 <b>System Status</b>\n"
        f"{'━' * 28}\n\n"

        f"<b>🔧 System</b>\n"
        f"  ├ <b>OS:</b> <code>{os_name} {os_release}</code> [{os_arch}]\n"
        f"  ├ <b>Host:</b> <code>{hostname}</code>\n"
        f"  └ <b>Bot Uptime:</b> <code>{uptime}</code> ⚡️\n\n"

        f"<b>⚙️ CPU</b>\n"
        f"  ├ <b>Usage:</b> <code>{cpu_pct}%</code>  {progress_bar(cpu_pct)}\n"
        f"  ├ <b>Cores:</b> <code>{cpu_count_physical} physical / {cpu_count_logical} logical</code>\n"
        f"  └ <b>Frequency:</b> <code>{freq_str}</code>\n\n"

        f"<b>🧠 Memory</b>\n"
        f"  ├ <b>RAM:</b> <code>{ram_used} / {ram_total}</code> ({ram_pct}%)  {progress_bar(ram_pct)}\n"
        f"  ├ <b>Available:</b> <code>{ram_avail}</code>\n"
        f"  └ <b>Swap:</b> <code>{swap_used} / {swap_total}</code> ({swap_pct}%)  {progress_bar(swap_pct)}\n\n"

        f"<b>💾 Disk</b>\n"
        f"  ├ <b>Usage:</b> <code>{disk_used} / {disk_total}</code> ({disk_pct}%)  {progress_bar(disk_pct)}\n"
        f"  └ <b>Free:</b> <code>{disk_free}</code>\n\n"

        f"<b>🌐 Network</b>\n"
        f"  ├ <b>Sent:</b> <code>{net_sent}</code> ↑\n"
        f"  └ <b>Received:</b> <code>{net_recv}</code> ↓\n\n"

        f"<b>🤖 Bot Process</b>\n"
        f"  ├ <b>Memory:</b> <code>{bot_mem}</code>\n"
        f"  ├ <b>Threads:</b> <code>{bot_threads}</code>\n"
        f"  ├ <b>Python:</b> <code>{py_ver}</code> 🐍\n"
        f"  └ <b>Aiogram:</b> <code>{aiogram_ver}</code>\n"
    )

    await message.reply(text, parse_mode=ParseMode.HTML)


@router.message(Command("stats"), IsSudoUser())
async def stats(message: Message):
    from sqlalchemy import text
    from PglRobot.database.db_core import get_session

    bl = bl_c = filt = filt_c = dis = dis_c = 0
    fed_bans = feds = gbans = log_channels = 0
    notes = notes_c = rules_c = 0
    users = chats = warns = warns_c = warn_f = warn_f_c = 0

    async for session in get_session():

        async def get_stats(table_name: str, chat_col: str = "chat_id") -> tuple[int, int]:
            try:
                count = (await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))).scalar() or 0
                chats = (await session.execute(text(f"SELECT COUNT(DISTINCT {chat_col}) FROM {table_name}"))).scalar() or 0
                return int(count), int(chats)
            except Exception:
                return 0, 0

        async def get_count(table_name: str) -> int:
            try:
                val = (await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))).scalar() or 0
                return int(val)
            except Exception:
                return 0

        bl, bl_c = await get_stats("blacklist")
        filt, filt_c = await get_stats("cust_filters")
        dis, dis_c = await get_stats("disabled_commands")

        fed_bans = await get_count("bans_feds")
        feds = await get_count("feds")
        gbans = await get_count("gbans")
        log_channels = await get_count("log_channels")

        notes, notes_c = await get_stats("notes")
        rules_c = (await get_stats("rules"))[1]

        users = await get_count("users")
        chats = await get_count("chats")

        warns, warns_c = await get_stats("warns")
        warn_f, warn_f_c = await get_stats("warn_filters")

    out = (
        f"<b>📊 Current Stats:</b>\n"
        f"{'━' * 28}\n\n"
        f"<b>👥 Users & Chats</b>\n"
        f"  ├ <code>{users}</code> users across <code>{chats}</code> chats\n"
        f"  └ <code>{rules_c}</code> chats have rules set\n\n"
        f"<b>⚠️ Moderation</b>\n"
        f"  ├ <code>{warns}</code> total warns across <code>{warns_c}</code> chats\n"
        f"  ├ <code>{warn_f}</code> warn filters across <code>{warn_f_c}</code> chats\n"
        f"  ├ <code>{gbans}</code> globally banned users\n"
        f"  └ <code>{fed_bans}</code> fed-banned users across <code>{feds}</code> federations\n\n"
        f"<b>📋 Content</b>\n"
        f"  ├ <code>{notes}</code> notes across <code>{notes_c}</code> chats\n"
        f"  ├ <code>{filt}</code> filters across <code>{filt_c}</code> chats\n"
        f"  └ <code>{bl}</code> blacklist triggers across <code>{bl_c}</code> chats\n\n"
        f"<b>⚙️ Configuration</b>\n"
        f"  ├ <code>{log_channels}</code> log channels set\n"
        f"  └ <code>{dis}</code> disabled commands across <code>{dis_c}</code> chats"
    )
    await message.reply(out, parse_mode=ParseMode.HTML)


__help__ = """
<b>🖥️ Sysinfo</b> <i>(Sudo only)</i>

- /sysinfo — Full system status: CPU, RAM, Disk, Network, Bot process info
- /stats — Database statistics across all groups
"""
from PglRobot.utils.help_system import register_help
register_help("Sysinfo", __help__)
