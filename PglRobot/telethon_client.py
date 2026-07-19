from telethon import TelegramClient
from PglRobot.config import Config

tbot = TelegramClient("PglRobot_telethon", Config.API_ID, Config.API_HASH)
