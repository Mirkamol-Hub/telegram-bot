"""
Telegram Bot Service
Handles outgoing messages and webhook registration.
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # e.g. https://yourapp.render.com/webhook/telegram
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


class BotService:

    async def set_webhook(self):
        if not WEBHOOK_URL or not BOT_TOKEN:
            logger.warning("BOT_TOKEN or WEBHOOK_URL not set — skipping webhook registration.")
            return
        url = f"{TELEGRAM_API}/setWebhook"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"url": f"{WEBHOOK_URL}/telegram"})
            data = resp.json()
            if data.get("ok"):
                logger.info(f"Webhook set: {WEBHOOK_URL}/telegram")
            else:
                logger.error(f"Webhook set failed: {data}")

    async def send_message(self, chat_id: str | int, text: str) -> bool:
        """Send a plain text message to a Telegram user."""
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not configured.")
            return False
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                data = resp.json()
                if not data.get("ok"):
                    logger.warning(f"send_message failed for {chat_id}: {data.get('description')}")
                    return False
                return True
        except Exception as e:
            logger.error(f"send_message exception for {chat_id}: {e}")
            return False

    async def send_homework_to_group(
        self,
        students: list[dict],
        group_name: str,
        homework_text: str,
        teacher_name: str,
    ) -> dict:
        """
        Send homework to all students in a group.
        Returns delivery report: {sent: [...], failed: [...]}.
        """
        sent, failed = [], []
        message = (
            f"📚 <b>Homework — {group_name}</b>\n\n"
            f"{homework_text}\n\n"
            f"<i>Sent by: {teacher_name}</i>"
        )
        for student in students:
            tid = str(student.get("Telegram_ID", "")).strip()
            name = student.get("Name", "Unknown")
            if not tid or tid == "0":
                failed.append({"name": name, "reason": "No Telegram ID"})
                continue
            success = await self.send_message(tid, message)
            if success:
                sent.append(name)
            else:
                failed.append({"name": name, "reason": "Delivery failed"})
        return {"sent": sent, "failed": failed}

    async def send_mini_app_button(self, chat_id: str | int):
        """Send welcome message with Mini App launch button."""
        mini_app_url = os.getenv("MINI_APP_URL", WEBHOOK_URL.replace("/webhook", ""))
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": "👋 Welcome to <b>Learning Center ERP</b>!\n\nTap the button below to open the app:",
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [[
                    {
                        "text": "📱 Open ERP App",
                        "web_app": {"url": mini_app_url},
                    }
                ]]
            },
        }
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload)
