# 📚 Learning Center ERP+CRM

A production-ready **Telegram Mini App** for private learning centers.  
Manage groups, attendance, homework delivery, and expenses — all inside Telegram.

---

## Features

| Module | Admin | Teacher | Student |
|--------|-------|---------|---------|
| 👥 Groups — view & create | ✅ | 👁 view | — |
| 📋 Attendance — mark present/absent | ✅ | ✅ | — |
| 📝 Homeworks — send via Telegram | ✅ | ✅ | 📩 receives |
| 💰 Expenses — track costs | ✅ | — | — |
| 🤖 Bot registration flow | auto | auto | ✅ |

---

## Quick Start

```bash
# 1. Clone
git clone <repo-url>
cd erp-crm

# 2. Configure
cp .env.example .env
# Fill in your Telegram Bot Token, Google Sheet ID, and service account

# 3. Install & run
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Full setup: see **[docs/SETUP.md](docs/SETUP.md)**

---

## Project Structure

```
erp-crm/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt
│   ├── routers/
│   │   ├── auth.py             # Auth verification endpoint
│   │   ├── groups.py           # Groups CRUD
│   │   ├── attendance.py       # Attendance submit/query
│   │   ├── homeworks.py        # Homework send + history
│   │   ├── expenses.py         # Expense tracking
│   │   ├── students.py         # Student list
│   │   └── webhook.py          # Telegram bot webhook handler
│   └── services/
│       ├── sheets.py           # Google Sheets data access layer
│       ├── bot.py              # Telegram messaging service
│       └── auth.py             # initData validation + role resolution
├── frontend/
│   └── index.html              # Telegram Mini App (single-file)
├── docs/
│   └── SETUP.md                # Full setup & deployment guide
├── .env.example                # Environment variables template
├── render.yaml                 # Render.com deployment config
└── railway.toml                # Railway.app deployment config
```

---

## Stack

- **Backend**: Python 3.11 + FastAPI + uvicorn
- **Bot**: Telegram Bot API (webhook mode)
- **Frontend**: Vanilla HTML/CSS/JS (Telegram Mini App)
- **Database**: Google Sheets via gspread
- **Auth**: Telegram WebApp `initData` HMAC validation

---

## Deployment

| Platform | Config file | Notes |
|----------|-------------|-------|
| Render.com | `render.yaml` | Free tier, auto-deploy from GitHub |
| Railway.app | `railway.toml` | Fast deploys, simple UI |
| VPS (Ubuntu) | Manual | See docs/SETUP.md |

---

## License

MIT — free to use and modify for your learning center.
