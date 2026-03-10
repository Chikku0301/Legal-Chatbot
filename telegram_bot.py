#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Legal Aid Bot — Telegram Interface
Run with:  python telegram_bot.py
"""

import os
import sys
import logging
import datetime
import asyncio

from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ─── Ensure project root is on sys.path ──────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from core.classifier import classify_dispute, get_workflow
from core.document_generator import generate_text_document, txt_to_pdf
from core.tracker import OUTPUT_DIR, create_case, check_reminders, get_case_tracker_text
from core.session import get_user_session, update_user_session, clear_user_session, State
from core.llm_helper import get_field_help

# ─── Load env ─────────────────────────────────────────────────────────────────
load_dotenv(os.path.join(PROJECT_DIR, ".env"))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌  TELEGRAM_BOT_TOKEN not found in .env file!")
    sys.exit(1)

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ═════════════════════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point — /start command."""
    user_id = update.effective_user.id
    
    # Reset user session for a fresh start
    clear_user_session(user_id)
    update_user_session(user_id, new_state=State.START)

    await update.message.reply_text(
        "⚖️ *LEGAL AID BOT*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Citizen Legal Assistance System\n\n"
        "ℹ️ _This system provides procedural guidance only — not legal advice._\n\n"
        "I can help you with disputes like:\n"
        "• Security deposit / rent recovery\n"
        "• Employment / salary disputes\n"
        "• Consumer complaints\n"
        "• Cheque bounce / loan recovery\n"
        "• Contract disputes\n"
        "• Partition suits\n"
        "• Succession / probate\n"
        "• Cybercrime complaints\n"
        "• Child custody\n"
        "• Insurance disputes\n"
        "• Defamation suits\n"
        "• Public interest litigation\n"
        "• Government service / tax disputes\n"
        "• And more…\n\n"
        "👤 *Please tell me your name to begin.*",
        parse_mode="Markdown",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation."""
    user_id = update.effective_user.id
    clear_user_session(user_id)
    await update.message.reply_text(
        "❌ Session cancelled.\n\n"
        "Send /start anytime to begin a new session.\n"
        "Good luck! ⚖️"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show reminders for pending cases — /status command."""
    reminders = await asyncio.to_thread(check_reminders)
    if not reminders:
        await update.message.reply_text("✅ No pending reminders at this time.")
        return

    lines = ["🔔 *PENDING REMINDERS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for case, days_left in reminders:
        urgency = "🔴" if days_left <= 3 else "🟡"
        lines.append(
            f"{urgency} *Case {case['case_id']}*: "
            f"{case['deadline_label']} in *{days_left} day(s)* — {case['next_deadline']}"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ═════════════════════════════════════════════════════════════════════════════
#  CONCURRENT ROUTER
# ═════════════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes incoming text messages to their specific handlers asynchronously."""
    asyncio.create_task(_process_user_message(update, context))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes incoming inline button callbacks asynchronously."""
    asyncio.create_task(_process_user_callback(update, context))


async def _process_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process normal text messages based on persistent DB state."""
    user_id = update.effective_user.id
    message = update.message.text.strip()
    
    session = get_user_session(user_id)
    state = session.get("state")

    if state == State.START:
        await ask_name_received(update, message, user_id, session)
    elif state == State.ASK_PROBLEM:
        await ask_problem_received(update, message, user_id, session)
    elif state == State.COLLECT_INFO:
        await collect_info_received(update, message, user_id, session)
    elif state == State.DONE:
        # Prompt them to /start to use the bot again
        await update.message.reply_text("Your session is complete. Please type /start to begin a new one.")
    else:
        # Catch unexpected state
        await update.message.reply_text("I didn't expect a message right now. If you're stuck, type /start.")


async def _process_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process inline keyboard responses based on DB state."""
    user_id = update.effective_user.id
    query = update.callback_query
    await query.answer()
    
    session = get_user_session(user_id)
    state = session.get("state")
    data = query.data
    
    if state == State.ASK_DOCS and data.startswith("docs_"):
        await docs_callback(update, query, user_id, session)
    elif state == State.ASK_TRACKER and data.startswith("track_"):
        await tracker_callback(update, query, user_id, session)
    else:
        await query.edit_message_text("❌ This button has expired or is invalid for your current step.")


# ═════════════════════════════════════════════════════════════════════════════
#  WORKFLOW HANDLERS
# ═════════════════════════════════════════════════════════════════════════════

async def ask_name_received(update: Update, message: str, user_id: int, session: dict):
    """User sent their name → ask for problem description."""
    update_user_session(user_id, new_state=State.ASK_PROBLEM, updates={"user_name": message})

    await update.message.reply_text(
        f"Hello *{message}*! 👋\n\n"
        "📝 *Please describe your legal problem in your own words.*\n\n"
        "For example: My landlord is not returning my security deposit of Rs.50,000",
        parse_mode="Markdown",
    )


async def ask_problem_received(update: Update, message: str, user_id: int, session: dict):
    """User described the problem → classify and show workflow."""
    
    # Offload blocking ML classification to background thread
    category, process, court = await asyncio.to_thread(classify_dispute, message)
    workflow = await asyncio.to_thread(get_workflow, category)

    session_updates = {
        "user_message": message,
        "category": category,
        "process": process,
        "court": court,
        "workflow": workflow
    }
    update_user_session(user_id, new_state=State.ASK_DOCS, updates=session_updates)

    # Build step list
    steps_text = "\n".join(
        f"  {i}. {s}" for i, s in enumerate(workflow["steps"], 1)
    )

    await update.message.reply_text(
        "🧠 *AI DISPUTE CLASSIFICATION*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📂 Dispute Category:  *{category}*\n"
        f"📋 Legal Process:     *{process}*\n"
        f"🏛 Recommended Court: *{court}*\n\n"
        f"📚 *{workflow['title']}*\n\n"
        "⚠️ _DISCLAIMER: This system provides procedural guidance only "
        "and does not constitute legal advice._\n\n"
        "*Step-by-step legal process:*\n"
        f"{steps_text}\n\n"
        f"⏱ Estimated time: *{workflow['time_estimate']}*",
        parse_mode="Markdown",
    )

    # Ask about documents
    docs_text = "\n".join(f"  • {d}" for d in workflow["documents_needed"])

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, I have them", callback_data="docs_yes"),
            InlineKeyboardButton("❌ Some are missing", callback_data="docs_no"),
        ]
    ])

    await update.message.reply_text(
        "📄 *Do you have the key documents for this case?*\n\n"
        "*Required documents:*\n"
        f"{docs_text}\n",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def docs_callback(update: Update, query, user_id: int, session: dict):
    """Handle documents readiness inline button."""
    workflow = session["data"]["workflow"]
    
    if query.data == "docs_no":
        docs_warning = "\n".join(f"  ⚠ {d}" for d in workflow["documents_needed"])
        await query.edit_message_text(
            "⚠️ *DOCUMENT WARNING*\n\n"
            "Cases without key documents may face scrutiny during filing.\n"
            "Try to obtain the following before filing:\n\n"
            f"{docs_warning}\n\n"
            "_We will continue with your available information._",
            parse_mode="Markdown",
        )
    else:
        await query.edit_message_text("✅ Great! You have the required documents.")

    # Start collecting case info
    questions = workflow["questions"]
    
    session_data_updates = {
        "questions": questions,
        "q_index": 0,
        "case_data": {
            "user_name": session["data"]["user_name"],
            "phone": "telegram_user",
            "court": session["data"]["court"],
            "city": "Chennai",
        }
    }
    
    update_user_session(user_id, new_state=State.COLLECT_INFO, updates=session_data_updates)

    # Ask the first question
    _, label = questions[0]
    await query.message.reply_text(
        "📝 *CASE DETAILS COLLECTION*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "_Please answer the following questions.\n"
        "Send 'skip' to skip an optional field.\n"
        "Send '?' or 'help' if you're not sure what to enter._\n\n"
        f"❓ *Question 1/{len(questions)}:*\n"
        f"{label}",
        parse_mode="Markdown",
    )


async def collect_info_received(update: Update, message: str, user_id: int, session: dict):
    """Collect answers to workflow-specific questions one by one. Or invoke LLM helper."""
    answer = message
    questions = session["data"]["questions"]
    q_index = session["data"]["q_index"]
    case_data = session["data"]["case_data"]
    
    field_key, field_label = questions[q_index]

    # Check for help triggers
    if answer.lower() in ["?", "help", "what is this", "explain"]:
        # Show typing indicator while LLM generates
        await update.message.reply_chat_action(action="typing")
        
        # Offload Groq network call to background thread
        help_text = await asyncio.to_thread(
            get_field_help,
            session["data"]["category"],
            session["data"]["workflow"]["title"],
            field_key,
            field_label,
            case_data,  # Has all previously collected answers
            questions
        )
        
        await update.message.reply_text(
            f"💡 *Field Info:*\n{help_text}\n\n"
            f"Now, please answer:\n❓ *Question {q_index + 1}/{len(questions)}:*\n{field_label}",
            parse_mode="Markdown"
        )
        # We don't advance the state or q_index, wait for their actual answer
        return

    # Normal answer handling (Save answer unless skipped)
    if answer.lower() != "skip":
        case_data[field_key] = answer

    # Move to next question
    q_index += 1
    
    update_user_session(user_id, updates={"q_index": q_index, "case_data": case_data})

    if q_index < len(questions):
        _, next_label = questions[q_index]
        await update.message.reply_text(
            f"❓ *Question {q_index + 1}/{len(questions)}:*\n"
            f"{next_label}",
            parse_mode="Markdown",
        )
        return

    # All questions answered → generate document
    update_user_session(user_id, new_state=State.ASK_TRACKER) # We wait here until doc completes
    await generate_document(update, user_id, session)


async def generate_document(update: Update, user_id: int, session: dict):
    """Generate the petition and send it as a file (offloaded to thread)."""
    await update.message.reply_text("⚙️ _Generating your legal petition document…_", parse_mode="Markdown")

    # Fetch fresh session state to ensure case_data has the absolute latest
    session = get_user_session(user_id)
    case_data = session["data"]["case_data"]
    workflow = session["data"]["workflow"]
    court = session["data"]["court"]

    safe_name = case_data["user_name"].replace(" ", "_")
    txt_filename = f"Legal_Petition_{safe_name}.txt"
    pdf_filename = f"Legal_Petition_{safe_name}.pdf"
    txt_path = os.path.join(OUTPUT_DIR, txt_filename)
    pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)

    # Generate text document (Blocking CPU operation — offload to thread)
    success_gen = await asyncio.to_thread(generate_text_document, case_data, workflow, txt_path)

    # Convert to PDF (Blocking CPU operation — offload to thread)
    pdf_gen = False
    if success_gen:
        pdf_gen = await asyncio.to_thread(txt_to_pdf, txt_path, pdf_path)

    # Send the file(s)
    if success_gen:
        if pdf_gen and os.path.exists(pdf_path):
            await update.message.reply_document(
                document=open(pdf_path, "rb"),
                filename=pdf_filename,
                caption="📄 Your Legal Petition (PDF)",
            )
        if os.path.exists(txt_path):
            await update.message.reply_document(
                document=open(txt_path, "rb"),
                filename=txt_filename,
                caption="📄 Your Legal Petition (Text)",
            )

        await update.message.reply_text(
            "✅ *Your legal petition draft is ready!*\n\n"
            "*Next steps:*\n"
            "  1. Download and review the document carefully\n"
            "  2. Fill in any missing details\n"
            "  3. Get it verified by a local advocate if possible\n"
            "  4. Print 3 copies before filing",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("⚠️ Document generation failed. Please try again with /start.")
        update_user_session(user_id, new_state=State.DONE)
        return

    # Procedural guidance
    docs_text = "\n".join(f"     • {d}" for d in workflow["documents_needed"])
    await update.message.reply_text(
        f"🧭 *NEXT STEPS — Filing in {court}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "1. Print the complaint document (3 copies)\n"
        "2. Attach all supporting documents:\n"
        f"{docs_text}\n"
        f"3. Court filing fee: {workflow['court_fee']}\n"
        "4. Visit the court registry during working hours\n"
        "   _(usually 10 AM – 1 PM on weekdays)_\n"
        "5. Submit documents and obtain filing number\n"
        "6. Keep all receipts and acknowledgements safely",
        parse_mode="Markdown",
    )

    # Ask about case tracking
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, track my case", callback_data="track_yes"),
            InlineKeyboardButton("❌ No thanks", callback_data="track_no"),
        ]
    ])

    await update.message.reply_text(
        "📅 *Would you like to create a case tracking entry?*\n\n"
        "This will:\n"
        "  ✅ Track your deadlines\n"
        "  ✅ Send reminders before important dates\n"
        "  ✅ Prepare you for hearings",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    # State is already ASK_TRACKER from earlier


async def tracker_callback(update: Update, query, user_id: int, session: dict):
    """Handle case tracker inline button."""
    case_data = session["data"]["case_data"]
    workflow = session["data"]["workflow"]
    court = session["data"]["court"]
    category = session["data"]["category"]
    process = session["data"]["process"]
    user_name = session["data"]["user_name"]

    case_id = None

    if query.data == "track_yes":
        # DB operation — offload
        case_id = await asyncio.to_thread(create_case, case_data, workflow, court)

        # Show case tracker
        tracker_text = await asyncio.to_thread(get_case_tracker_text, case_id)
        await query.edit_message_text(f"✅ Case created!\n\n{tracker_text}")

        # Reminders
        deadline_dt = datetime.date.today() + datetime.timedelta(days=30)
        hearing_dt = datetime.date.today() + datetime.timedelta(days=45)

        await query.message.reply_text(
            "🔔 *AUTOMATIC REMINDERS SCHEDULED*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Evidence Submission Deadline: *{deadline_dt.strftime('%d %B %Y')}*\n"
            f"   → Reminder: 3 days before ({(deadline_dt - datetime.timedelta(days=3)).strftime('%d %B %Y')})\n\n"
            f"📌 First Hearing: *{hearing_dt.strftime('%d %B %Y')}*\n"
            f"   → Reminder: 2 days before ({(hearing_dt - datetime.timedelta(days=2)).strftime('%d %B %Y')})\n\n"
            "_Use /status anytime to check your case reminders._",
            parse_mode="Markdown",
        )

        # Hearing preparation
        docs_checklist = "".join(f"  ☐ {d}\n" for d in workflow["documents_needed"])
        await query.message.reply_text(
            "📋 *HEARING PREPARATION CHECKLIST*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "*Documents to bring on the hearing day:*\n"
            "  ☐ Filed complaint / petition copy\n"
            f"{docs_checklist}"
            "  ☐ Government ID proof\n"
            "  ☐ Any correspondence with the respondent\n\n"
            "*In the courtroom:*\n"
            "  • Speak clearly and respectfully to the judge\n"
            "  • Present facts briefly and stick to the point\n"
            "  • Submit evidence when the judge requests\n"
            "  • Do not interrupt the opposing party\n"
            "  • Request an interpreter if needed",
            parse_mode="Markdown",
        )
    else:
        await query.edit_message_text("👍 No problem, case tracking skipped.")

    # Error prevention check
    missing = []
    if "deposit_amount" in case_data or "amount_due" in case_data:
        if not case_data.get("property_address") and not case_data.get("employer_address"):
            missing.append("Respondent Address")
    if not case_data.get("user_name"):
        missing.append("Complainant Name")

    if missing:
        missing_text = "\n".join(f"  ⚠ {m}" for m in missing)
        await query.message.reply_text(
            "⚠️ *COMPLETENESS WARNING*\n\n"
            "The following may need to be added before filing:\n"
            f"{missing_text}\n\n"
            "_Please review your petition before submitting._",
            parse_mode="Markdown",
        )

    # Final summary
    summary = (
        "🎉 *SESSION COMPLETE — SUMMARY*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 User:     *{user_name}*\n"
        f"📂 Dispute:  *{category}*\n"
        f"📋 Process:  *{process}*\n"
        f"🏛 Court:    *{court}*\n"
    )
    if case_id:
        summary += f"🆔 Case ID:  *{case_id}*\n"

    summary += (
        "\n✅ *You have completed the legal guidance session.*\n\n"
        "*Your next actions:*\n"
        "  → Review and print the generated petition\n"
        f"  → Visit {court} during filing hours\n"
        "  → Carry all supporting documents\n\n"
        "⚠️ _This is procedural guidance. For legal representation, "
        "consult a qualified advocate._\n\n"
        "Good luck with your case! ⚖️\n\n"
        "_Send /start to begin a new session._"
    )

    await query.message.reply_text(summary, parse_mode="Markdown")
    
    # Update state to Done and wipe form data
    update_user_session(user_id, new_state=State.DONE, updates={})


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    """Start the Telegram bot."""
    from telegram.request import HTTPXRequest

    # Use generous timeouts to avoid TimedOut errors on slow networks
    request = HTTPXRequest(
        connect_timeout=20.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .request(request)
        .build()
    )

    # Add Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("status", status_command))

    # Add Generalized Async Routers for messages and callbacks
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Start polling
    print("⚖️ Legal Aid Bot running (Multi-User Async Server)!")
    print("   Press Ctrl+C to stop.\n")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
