import os
from dotenv import load_dotenv

from typing import final

load_dotenv()

@final
class Config(object):
    # NSFW API (Sightengine)
    SIGHTENGINE_API_USER = os.environ.get("SIGHTENGINE_API_USER", "")
    SIGHTENGINE_API_SECRET = os.environ.get("SIGHTENGINE_API_SECRET", "")
    LOGGER = os.environ.get("LOGGER", "True").lower() in ("true", "1", "yes")
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    TOKEN = os.environ.get("TOKEN", "")
    OWNER_ID = int(os.environ.get("OWNER_ID", 0))
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "")
    EVENT_LOGS = int(os.environ.get("EVENT_LOGS", 0))
    
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")
    
    SUDO_USERS = {int(x) for x in os.environ.get("SUDO_USERS", "").split()} | {OWNER_ID}
    DEV_USERS = {int(x) for x in os.environ.get("DEV_USERS", "").split()} | {OWNER_ID}
    BL_CHATS: set[int] = set()


