import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL", None)

# Search timeout in seconds
SEARCH_TIMEOUT = 15

# Max image size for download (MB)
MAX_IMAGE_SIZE = 20
