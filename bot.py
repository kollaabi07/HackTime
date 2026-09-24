"""
bot.py
------
Entry point for the Telegram bot.

Responsibilities:
- Load configuration (bot token) from environment variables via config.py
- Set up logging
- Register all command and message handlers
- Start the bot using long polling (no public URL / webhook needed —
  perfect for local development and hackathon demos)

Run with:
    python bot.py
"""

import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import TelegramError

from config import TELEGRAM_BOT_TOKEN
from utils.logger import setup_logging
from handlers.commands import (
    check_command,
    error_handler,
    help_command,
    save_command,
    setjob_command,
    shortlist_command,
    start_command,
)
from handlers.messages import echo_message

# Set up logging as early as possible so every module can use logging.getLogger(__name__)
setup_logging()
logger = logging.getLogger(__name__)


def build_application() -> Application:
    """
    Creates the Telegram Application object and registers all handlers.
    Keeping this in its own function makes the bot easy to unit test later
    (you can build the app without calling run_polling()).
    """
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # --- Command handlers ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("setjob", setjob_command))
    application.add_handler(CommandHandler("check", check_command))
    application.add_handler(CommandHandler("save", save_command))
    application.add_handler(CommandHandler("shortlist", shortlist_command))

    # --- Message handler (catches any plain text that isn't a command) ---
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message)
    )

    # --- Global error handler (catches exceptions raised inside any handler) ---
    application.add_error_handler(error_handler)

    return application


def main() -> None:
    logger.info("Starting Telegram bot...")

    try:
        application = build_application()
    except Exception:
        # This typically means the token is missing/invalid at construction time
        logger.exception("Failed to build the bot application. Check your TELEGRAM_BOT_TOKEN.")
        raise

    try:
        # run_polling() blocks and keeps the bot alive until you press Ctrl+C
        application.run_polling(allowed_updates=["message", "callback_query"])
    except TelegramError:
        logger.exception("A Telegram API error occurred while polling.")
    except KeyboardInterrupt:
        logger.info("Bot stopped manually (Ctrl+C).")
    except Exception:
        logger.exception("Unexpected error while running the bot.")


if __name__ == "__main__":
    main()
