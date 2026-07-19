import asyncio
import logging
from logging.handlers import RotatingFileHandler
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from PglRobot.config import Config
from PglRobot.telethon_client import tbot
from PglRobot.database.db_core import init_db

# Setup logging with rotation — max 2MB per file, keep 3 backups
rotating_handler = RotatingFileHandler(
    "log.txt", maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
rotating_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        rotating_handler,
        logging.StreamHandler()
    ]
)

# Suppress noisy aiogram internal logs — only show WARNING and above
logging.getLogger("aiogram.event").setLevel(logging.WARNING)
logging.getLogger("aiogram.dispatcher").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing database...")
    await init_db()

    bot = Bot(
        token=Config.TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Global error handler
    from aiogram.types import ErrorEvent
    import traceback
    import html
    @dp.errors()
    async def global_error_handler(event: ErrorEvent):
        logger.error(f"Update caused error: {event.exception}", exc_info=event.exception)
        if Config.EVENT_LOGS != 0:
            tb = "".join(traceback.format_exception(type(event.exception), event.exception, event.exception.__traceback__))
            msg = f"<b>⚠️ Exception in PglRobot!</b>\n\n<b>Error:</b> <code>{html.escape(str(event.exception))}</code>\n\n<pre>{html.escape(tb[-3500:])}</pre>"
            try:
                await bot.send_message(Config.EVENT_LOGS, msg, parse_mode=ParseMode.HTML)
            except Exception:
                pass
    
    # Import and register routers
    from PglRobot.plugins import (
        users, admin, sysinfo, afk, 
        antispam, rules, notes, purge,
        log_channel, help, welcome, nightmode, karma, gban, feds, zombies,
        approvals, trust, locks, blacklists, join_requests, fsub, nsfw,
        connections, filters, userinfo, bans, muting, warns,
        reports, antiflood, tagall, antiraid, disable, broadcast
    )
    dp.include_router(help.help_router)
    dp.include_router(rules.rules_router)
    dp.include_router(users.router)
    dp.include_router(admin.router)
    dp.include_router(sysinfo.router)
    dp.include_router(afk.afk_router)
    dp.include_router(antispam.antispam_router)
    dp.include_router(notes.notes_router)
    dp.include_router(purge.purge_router)
    dp.include_router(log_channel.log_router)
    dp.include_router(welcome.welcome_router)
    dp.include_router(nightmode.nightmode_router)
    dp.include_router(karma.karma_router)
    dp.include_router(gban.gban_router)
    dp.include_router(feds.feds_router)
    dp.include_router(zombies.zombies_router)
    dp.include_router(approvals.approvals_router)
    dp.include_router(trust.trust_router)
    dp.include_router(locks.locks_router)
    dp.include_router(blacklists.blacklists_router)
    dp.include_router(join_requests.join_requests_router)
    dp.include_router(fsub.fsub_router)
    dp.include_router(nsfw.nsfw_router)
    dp.include_router(connections.connections_router)
    dp.include_router(filters.filters_router)
    dp.include_router(userinfo.userinfo_router)
    dp.include_router(bans.bans_router)
    dp.include_router(muting.muting_router)
    dp.include_router(warns.warns_router)
    dp.include_router(reports.reports_router)
    dp.include_router(antiflood.antiflood_router)
    dp.include_router(tagall.tagall_router)
    dp.include_router(antiraid.antiraid_router)
    dp.include_router(disable.disable_router)
    dp.include_router(broadcast.broadcast_router)
    
    loaded_plugins = [
        "users", "admin", "sysinfo", "afk", "antispam", "rules", "notes", "purge",
        "log_channel", "help", "welcome", "nightmode", "karma", "gban", "feds", "zombies",
        "approvals", "trust", "locks", "blacklists", "join_requests", "fsub", "nsfw",
        "connections", "filters", "userinfo", "bans", "muting", "warns",
        "reports", "antiflood", "tagall", "antiraid", "disable", "broadcast"
    ]
    logger.info(f"Successfully loaded {len(loaded_plugins)} plugins: {', '.join(loaded_plugins)}")
    
    # --- DEBUG MIDDLEWARE ---
    # from aiogram import BaseMiddleware
    # from aiogram.types import Update
    # import json
    # 
    # class DebugUpdateMiddleware(BaseMiddleware):
    #     async def __call__(self, handler, event, data):
    #         # Log raw update to the standard logger
    #         if isinstance(event, Update) and event.message:
    #             logger.error(f"RAW UPDATE RECEIVED: {event.message.text}")
    #         return await handler(event, data)
    #         
    # dp.update.outer_middleware(DebugUpdateMiddleware())
    # ------------------------

    # --- TRACK USERS MIDDLEWARE ---
    from PglRobot.utils.track_middleware import TrackUsersMiddleware
    dp.update.outer_middleware(TrackUsersMiddleware())
    # ------------------------------

    # --- DISABLE COMMANDS MIDDLEWARE ---
    from PglRobot.utils.disable_middleware import DisableMiddleware
    dp.update.outer_middleware(DisableMiddleware())
    # -----------------------------------

    # Load startup caches
    from PglRobot.database.log_channel_sql import load_log_channels
    from PglRobot.database.warns_sql import load_chat_warn_filters
    from PglRobot.database.antiflood_sql import load_flood_settings
    from PglRobot.database.disable_sql import load_disabled_commands
    
    await load_log_channels()
    await load_chat_warn_filters()
    await load_flood_settings()
    await load_disabled_commands()

    logger.info("Starting bot...")
    await gban.load_gban_cache()
    await bot.delete_webhook(drop_pending_updates=True)
    nightmode.setup_nightmode(bot)
    
    # Start telethon client
    await tbot.start(bot_token=Config.TOKEN) # pyright: ignore[reportGeneralTypeIssues]
    logger.info("Telethon client started.")
    
    if Config.EVENT_LOGS != 0:
        try:
            await bot.send_message(
                Config.EVENT_LOGS, 
                "🤖 <b>PglRobot</b> has successfully started up and is running flawlessly!", 
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send startup log to EVENT_LOGS: {e}")
            
    # Start dummy web server for Render/Cloud health checks
    async def health_check(request):
        return web.Response(text="PglRobot is running natively!")
        
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Dummy web server started on port {port} for health checks.")
            
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
