"""
Telegram Webhook — receives all bot updates.
Handles /start and the student registration conversation flow.
"""

import os
import logging
from fastapi import APIRouter, Request, HTTPException
from services.sheets import SheetsService
from services.bot import BotService

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory conversation state (for small scale; replace with Redis for production)
# {telegram_id: {"step": "name"|"phone"|"group", "data": {...}}}
_conversation_state: dict = {}


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """Handle all incoming Telegram updates."""
    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    user = message.get("from", {})
    telegram_id = str(user.get("id", ""))
    first_name = user.get("first_name", "")

    sheets = SheetsService()
    bot = BotService()

    # ── /start command ────────────────────────────────────────────────────
    if text.startswith("/start"):
        # Check if admin/teacher → show mini app button
        role = sheets.get_user_role(telegram_id)
        if role in ("admin", "teacher"):
            await bot.send_mini_app_button(chat_id)
            return {"ok": True}

        # Check if already registered student
        if sheets.student_exists(telegram_id):
            student = sheets.get_student_by_telegram_id(telegram_id)
            await bot.send_message(
                chat_id,
                f"👋 Welcome back, <b>{student['Name']}</b>!\n"
                f"Group: {student['Group']}\n\n"
                "You will receive homework messages here automatically."
            )
            return {"ok": True}

        # Start registration
        _conversation_state[telegram_id] = {"step": "name", "data": {}}
        await bot.send_message(
            chat_id,
            f"👋 Hello, <b>{first_name}</b>! Welcome to the Learning Center.\n\n"
            "Let's get you registered. What is your <b>full name</b>?"
        )
        return {"ok": True}

    # ── Registration flow ─────────────────────────────────────────────────
    state = _conversation_state.get(telegram_id)
    if state:
        step = state["step"]

        if step == "name":
            state["data"]["name"] = text
            state["step"] = "phone"
            await bot.send_message(chat_id, "📱 Please enter your <b>phone number</b>:")

        elif step == "phone":
            state["data"]["phone"] = text
            # Show available groups
            groups = sheets.get_all_groups()
            if not groups:
                await bot.send_message(chat_id, "⚠️ No groups available yet. Contact your teacher.")
                del _conversation_state[telegram_id]
                return {"ok": True}
            group_list = "\n".join([f"• {g['Group_Name']}" for g in groups])
            state["step"] = "group"
            await bot.send_message(
                chat_id,
                f"📚 Available groups:\n{group_list}\n\n"
                "Please type the <b>exact group name</b> you belong to:"
            )

        elif step == "group":
            group_name = text
            groups = sheets.get_all_groups()
            valid = [g["Group_Name"] for g in groups]
            if group_name not in valid:
                await bot.send_message(
                    chat_id,
                    f"❌ Group '{group_name}' not found. Please choose from:\n" +
                    "\n".join([f"• {g}" for g in valid])
                )
                return {"ok": True}

            try:
                data = state["data"]
                student = sheets.add_student(
                    name=data["name"],
                    phone=data["phone"],
                    telegram_id=telegram_id,
                    group=group_name,
                )
                del _conversation_state[telegram_id]
                await bot.send_message(
                    chat_id,
                    f"✅ <b>Registration complete!</b>\n\n"
                    f"Name: {student['Name']}\n"
                    f"Group: {student['Group']}\n"
                    f"ID: {student['Student_ID']}\n\n"
                    "You will now receive homework messages here. 📚"
                )
            except ValueError as e:
                await bot.send_message(chat_id, f"⚠️ {e}")
                del _conversation_state[telegram_id]

        return {"ok": True}

    # ── Unrecognized message ──────────────────────────────────────────────
    role = sheets.get_user_role(telegram_id)
    if role in ("admin", "teacher"):
        await bot.send_mini_app_button(chat_id)
    else:
        await bot.send_message(
            chat_id,
            "Send /start to register or receive homework updates."
        )

    return {"ok": True}
