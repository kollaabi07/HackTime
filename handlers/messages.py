"""
handlers/messages.py
---------------------
Handler for plain text messages (anything that isn't a slash command).

This bot uses plain text resumes as its main input, and evaluates them
against a job description.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.commands import JOB_DESCRIPTION, get_user_stage, set_user_stage
from utils.resume_match import build_candidate_summary, extract_text_from_pdf_bytes
from utils.storage import save_candidate

logger = logging.getLogger(__name__)


async def _handle_resume_text(update: Update, resume_text: str, chat_id: int) -> None:
    if ":" not in resume_text:
        await update.message.reply_text("Please send resumes in this format:\nName: resume text")
        return

    name, resume = resume_text.split(":", 1)
    name = name.strip()
    resume = resume.strip()
    if not name or not resume:
        await update.message.reply_text("Please send resumes in this format:\nName: resume text")
        return

    score = save_candidate(name, resume, JOB_DESCRIPTION)
    summary = build_candidate_summary(name, resume, JOB_DESCRIPTION)
    await update.message.reply_text(
        f"{summary}\n\n"
        "Send the next resume or type /shortlist to see the ranking."
    )


async def _handle_resume_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    chat_id = update.effective_chat.id
    if not document or not document.file_name.lower().endswith(".pdf"):
        await update.message.reply_text("Please upload a PDF resume file.")
        return

    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    resume_text = extract_text_from_pdf_bytes(bytes(file_bytes))

    if not resume_text.strip():
        await update.message.reply_text(
            "I could not read text from that PDF. Please upload a text-based PDF or paste the resume text instead."
        )
        return

    candidate_name = document.file_name.rsplit(".", 1)[0].strip() or "Uploaded Candidate"
    save_candidate(candidate_name, resume_text, JOB_DESCRIPTION)
    summary = build_candidate_summary(candidate_name, resume_text, JOB_DESCRIPTION)
    await update.message.reply_text(
        f"{summary}\n\n"
        "Send the next resume or type /shortlist to see the ranking."
    )


async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles JD-first resume capture flow."""
    user = update.effective_user
    text = update.message.text

    logger.info("Message from user_id=%s: %s", user.id, text)

    try:
        if update.message.document is not None:
            await _handle_resume_document(update, context)
            return

        if not text or text.startswith("/"):
            return

        chat_id = update.effective_chat.id
        stage = get_user_stage(chat_id)

        if stage == "waiting_jd":
            global JOB_DESCRIPTION
            JOB_DESCRIPTION = text
            set_user_stage(chat_id, "waiting_resume")
            await update.message.reply_text(
                f"Job description saved: {JOB_DESCRIPTION}\n\n"
                "Now send each resume as:\n"
                "Name: resume text\n\n"
                "When finished, send /shortlist."
            )
            return

        if stage == "waiting_resume":
            await _handle_resume_text(update, text, chat_id)
            return

        await update.message.reply_text(
            "Please send the job description first with /setjob or /start.\n"
            "Then send resumes in this format:\nName: resume text"
        )

    except Exception:
        logger.exception("Error while handling text message from user_id=%s", user.id)
        await update.message.reply_text(
            "Sorry, I ran into an error handling that message."
        )
