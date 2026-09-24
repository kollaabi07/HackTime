"""
handlers/commands.py
---------------------
Handlers for Telegram bot commands (/start, /help) and a global error
handler that catches exceptions raised anywhere in the bot.

>>> THIS IS WHERE YOU'LL ADD YOUR HACKATHON FEATURE COMMANDS <<<
Add new functions here (e.g. `weather_command`, `ask_command`) following
the same pattern, then register them in bot.py with:
    application.add_handler(CommandHandler("weather", weather_command))
"""

import logging
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from utils.resume_match import build_candidate_summary, build_shortlist_report, score_resume_against_job
from utils.storage import get_ranked_candidates, save_candidate

logger = logging.getLogger(__name__)

JOB_DESCRIPTION = "Need Python developer with Django, SQL, REST APIs and teamwork"
USER_STAGE = {}


def get_user_stage(chat_id: int) -> str:
    return USER_STAGE.get(chat_id, "idle")


def set_user_stage(chat_id: int, stage: str) -> None:
    USER_STAGE[chat_id] = stage


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts the JD-first workflow."""
    user = update.effective_user
    logger.info("Received /start from user_id=%s username=%s", user.id, user.username)

    set_user_stage(update.effective_chat.id, "waiting_jd")
    await update.message.reply_text(
        f"Hi {user.first_name}! 👋\n\n"
        "First, send the job description (JD).\n"
        "After that, send each resume in this format:\n"
        "Name: resume text\n\n"
        "When you are done, send /shortlist."
    )


async def setjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets the current job description to match against."""
    if not context.args:
        await update.message.reply_text("Use: /setjob Python developer with Django SQL REST APIs")
        return

    global JOB_DESCRIPTION
    JOB_DESCRIPTION = " ".join(context.args)
    set_user_stage(update.effective_chat.id, "waiting_resume")
    await update.message.reply_text(
        f"Job description saved: {JOB_DESCRIPTION}\n\n"
        "Now send resumes one by one as:\n"
        "Name: resume text\n\n"
        "When finished, send /shortlist."
    )


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scores a single resume against the current job description."""
    text = update.message.text or ""
    resume_text = text.replace("/check", "", 1).strip()
    if not resume_text:
        await update.message.reply_text("Use: /check Python developer with Django and SQL")
        return

    score = score_resume_against_job(resume_text, JOB_DESCRIPTION)
    summary = build_candidate_summary("Candidate", resume_text, JOB_DESCRIPTION)
    await update.message.reply_text(summary)


async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Saves a candidate resume with a score for the current job description."""
    text = update.message.text or ""
    payload = text.replace("/save", "", 1).strip()
    if not payload or ":" not in payload:
        await update.message.reply_text("Use: /save Name: resume text")
        return

    name, resume = payload.split(":", 1)
    name = name.strip()
    resume = resume.strip()
    if not name or not resume:
        await update.message.reply_text("Use: /save Name: resume text")
        return

    score = save_candidate(name, resume, JOB_DESCRIPTION)
    set_user_stage(update.effective_chat.id, "waiting_resume")
    await update.message.reply_text(
        f"Saved {name} with score {score:.2f}/100 for this role.\n"
        "Send the next resume or type /shortlist to see the ranking."
    )


async def shortlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows the ranked shortlist for the current job description."""
    ranked = get_ranked_candidates(JOB_DESCRIPTION)
    report = build_shortlist_report(ranked, JOB_DESCRIPTION)
    set_user_stage(update.effective_chat.id, "idle")
    await update.message.reply_text(report)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Replies with a list of available commands when the user sends /help."""
    user = update.effective_user
    logger.info("Received /help from user_id=%s", user.id)

    await update.message.reply_text(
        "Available commands:\n"
        "/start - Greet the bot and check it's alive\n"
        "/setjob - Set the job description to compare against\n"
        "/check - Score a single resume\n"
        "/save - Save a candidate name and resume for the current job\n"
        "/shortlist - Show the ranked shortlist\n"
        "/help - Show this help message\n\n"
        "You can also upload a PDF resume or send resume text in plain chat."
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Global error handler, registered via application.add_error_handler().
    Catches any exception raised inside any handler so the bot never
    crashes silently, and logs the full traceback for debugging.
    """
    logger.error("Exception while handling an update:", exc_info=context.error)

    tb_string = "".join(
        traceback.format_exception(None, context.error, context.error.__traceback__)
    )
    logger.debug("Full traceback:\n%s", tb_string)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Something went wrong processing that. Please try again."
            )
        except Exception:
            logger.exception("Failed to send error notification to user.")
