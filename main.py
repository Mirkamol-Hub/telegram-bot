"""
ERP+CRM Mini App — FastAPI Backend
Telegram Bot + Google Sheets integration
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import groups, attendance, homeworks, expenses, students, auth, webhook
from services.sheets import SheetsService
from services.bot import BotService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    logger.info("Starting ERP-CRM backend...")
    sheets = SheetsService()
    await sheets.ensure_sheets_exist()
    bot = BotService()
    await bot.set_webhook()
    logger.info("All services initialized.")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Learning Center ERP+CRM",
    description="Telegram Mini App backend for private learning centers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(auth.router,       prefix="/api/auth",       tags=["auth"])
app.include_router(groups.router,     prefix="/api/groups",     tags=["groups"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["attendance"])
app.include_router(homeworks.router,  prefix="/api/homeworks",  tags=["homeworks"])
app.include_router(expenses.router,   prefix="/api/expenses",   tags=["expenses"])
app.include_router(students.router,   prefix="/api/students",   tags=["students"])
app.include_router(webhook.router,    prefix="/webhook",        tags=["webhook"])

# Serve Mini App frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ERP-CRM Mini App"}
