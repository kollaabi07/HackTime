"""
config.py
---------
Central place for loading configuration from environment variables.

This is the ONLY file that reads the .env file. Every other module imports
values from here instead of calling os.getenv() directly, so there's a
single source of truth and it's easy to see what config the bot needs.

The token itself is NEVER hardcoded — it must exist in a local .env file
(which should be in .gitignore) or be set as a real environment variable
on your deployment platform.
"""

import os
import sys
import logging

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load variables from a .env file in the project root into the environment.
# In production (e.g. Render, Railway, Docker) you'd typically set real
# environment variables instead, and load_dotenv() simply won't find a
# .env file there — that's fine, it fails silently.
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    logger.error(
        "TELEGRAM_BOT_TOKEN is not set. "
        "Create a .env file (see .env.example) with your BotFather token."
    )
    sys.exit(
        "ERROR: TELEGRAM_BOT_TOKEN environment variable is missing.\n"
        "1. Copy .env.example to .env\n"
        "2. Paste your token from @BotFather into .env\n"
    )

# Optional: log level can also be configured via env var, defaults to INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
