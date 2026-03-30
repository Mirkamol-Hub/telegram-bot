# Learning Center ERP+CRM — Complete Setup Guide

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites](#2-prerequisites)
3. [Telegram Bot Setup](#3-telegram-bot-setup)
4. [Google Sheets Setup](#4-google-sheets-setup)
5. [Local Development](#5-local-development)
6. [Deployment](#6-deployment)
7. [Sheet Structure Reference](#7-sheet-structure-reference)
8. [Environment Variables Reference](#8-environment-variables-reference)
9. [Role System](#9-role-system)
10. [API Reference](#10-api-reference)
11. [Troubleshooting](#11-troubleshooting)
12. [Scaling & Migration](#12-scaling--migration)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Client                       │
│          (Bot messages + Mini App WebView)               │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────────┐
│              FastAPI Backend (Python)                    │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐  │
│  │ /webhook │ │ /api/auth │ │/api/group│ │/api/...  │  │
│  └──────────┘ └───────────┘ └──────────┘ └──────────┘  │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Data Access Layer (SheetsService)      │   │
│  └──────────────────────┬───────────────────────────┘   │
└───────────────────────  │  ────────────────────────────┘
                          │ Google Sheets API
┌─────────────────────────▼───────────────────────────────┐
│                   Google Sheets                          │
│  Students | Groups | Attendance | Homeworks | Expenses   │
└─────────────────────────────────────────────────────────┘
```

**Data flow:**
- Teachers/Admins open the Mini App via Telegram → interact with backend API
- Students register via the Bot → receive homework as private messages
- All data persists in Google Sheets (single source of truth)

---

## 2. Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Backend runtime |
| pip | latest | Package manager |
| A Telegram account | — | Create bot & test |
| Google account | — | Sheets + Service Account |
| Git | any | Clone/deploy |

---

## 3. Telegram Bot Setup

### Step 1 — Create the bot

1. Open Telegram, search for **@BotFather**
2. Send `/newbot`
3. Choose a name: e.g. `Learning Center ERP`
4. Choose a username: e.g. `my_learning_center_bot`
5. Copy the **Bot Token** — looks like `7123456789:AAF...`

### Step 2 — Configure the Mini App

After deployment (Step 6), return to BotFather:

```
/newapp
→ select your bot
→ App title: Learning Center ERP
→ Short description: ERP for teachers and admins
→ Upload photo: (any 640×360 image)
→ Web App URL: https://your-app.onrender.com
```

### Step 3 — Set bot commands (optional)

Send to BotFather:
```
/setcommands
→ select your bot
→ paste:
start - Register or open the app
```

### Step 4 — Get your Telegram ID

- Message **@userinfobot** — it replies with your numeric user ID
- You'll need this for `ADMIN_IDS` and `TEACHER_IDS` env vars

---

## 4. Google Sheets Setup

### Step 1 — Create the spreadsheet

1. Go to [sheets.google.com](https://sheets.google.com)
2. Create a new blank spreadsheet
3. Name it: `Learning Center ERP`
4. Copy the **Spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
                                          ↑ copy this
   ```

### Step 2 — Create a Service Account

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or select existing)
3. Enable the **Google Sheets API**:
   - APIs & Services → Library → search "Google Sheets API" → Enable
4. Enable the **Google Drive API** (same steps)
5. Create Service Account:
   - APIs & Services → Credentials → Create Credentials → Service Account
   - Name: `erp-sheets-service`
   - Role: Editor
   - Click Done

### Step 3 — Download the key

1. Click your new Service Account → Keys tab
2. Add Key → Create new key → JSON
3. Download the `.json` file — keep it secret!

### Step 4 — Share the spreadsheet

1. Open the downloaded JSON file
2. Copy the `client_email` value (looks like `erp-sheets-service@project.iam.gserviceaccount.com`)
3. Open your Google Spreadsheet
4. Click Share → paste the email → set to **Editor** → Share

### Step 5 — Set environment variable

**Option A** (recommended for cloud): Convert the JSON to a single line and set as `GOOGLE_SERVICE_ACCOUNT_JSON`:
```bash
cat service_account.json | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)))"
```

**Option B** (local dev): Keep the file and set `GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json`

> The app will **automatically create all 5 sheets** with correct headers on first startup.

---

## 5. Local Development

### Clone and install

```bash
git clone <your-repo>
cd erp-crm

# Set up Python environment
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure environment

```bash
cp ../.env.example .env
# Edit .env with your values
```

Minimum required for local dev:
```env
TELEGRAM_BOT_TOKEN=your_token
GOOGLE_SPREADSHEET_ID=your_sheet_id
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
ADMIN_IDS=your_telegram_id
DEV_MODE=true
```

### Run the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Serve the frontend

The backend serves `frontend/` as static files. For local testing, simply open:
```
http://localhost:8000
```

Or open `frontend/index.html` directly in a browser (set `DEV_MODE=true` in backend).

### Expose locally for Telegram webhook (optional)

```bash
# Install ngrok
ngrok http 8000
# Copy the https URL → set as WEBHOOK_URL in .env
```

---

## 6. Deployment

### Option A — Render.com (recommended, free tier available)

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml`
5. Add environment variables in the Render dashboard
6. Click **Deploy**
7. Your app will be live at `https://your-app.onrender.com`

**After deploy:**
- Set `WEBHOOK_URL=https://your-app.onrender.com/webhook`
- Set `MINI_APP_URL=https://your-app.onrender.com`
- Redeploy (or the webhook registers automatically on startup)

### Option B — Railway.app

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

Set env vars in the Railway dashboard.

### Option C — Manual VPS (Ubuntu)

```bash
# Install dependencies
sudo apt update && sudo apt install python3.11 python3-pip nginx -y

# Clone and install
git clone <repo> /opt/erp-crm
cd /opt/erp-crm/backend
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/erp-crm.service << EOF
[Unit]
Description=Learning Center ERP
After=network.target

[Service]
WorkingDirectory=/opt/erp-crm/backend
EnvironmentFile=/opt/erp-crm/.env
ExecStart=/usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable erp-crm
sudo systemctl start erp-crm

# Nginx reverse proxy + SSL (certbot)
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

---

## 7. Sheet Structure Reference

The app auto-creates all sheets. Manual creation is not required.

### Sheet: Students

| Column | Type | Description |
|--------|------|-------------|
| Student_ID | String | Auto-generated (STU0001) |
| Name | String | Full name from registration |
| Phone | String | Phone from registration |
| Telegram_ID | Integer | Telegram user ID (for homework delivery) |
| Group | String | Group name |
| Join_Date | Date | YYYY-MM-DD |

### Sheet: Groups

| Column | Type | Description |
|--------|------|-------------|
| Group_ID | String | Auto-generated (GRP001) |
| Group_Name | String | Display name |
| Teacher | String | Teacher's name |
| Student_Count | Integer | Auto-updated on student add |

### Sheet: Attendance

| Column | Type | Description |
|--------|------|-------------|
| Date | Date | YYYY-MM-DD |
| Group | String | Group name |
| Student_ID | String | References Students.Student_ID |
| Student_Name | String | Denormalized for readability |
| Status | String | "Present" or "Absent" |

### Sheet: Homeworks

| Column | Type | Description |
|--------|------|-------------|
| Date | DateTime | YYYY-MM-DD HH:MM |
| Group | String | Group name |
| Homework_Text | String | Full homework content |
| Sent_By | String | Teacher's first name |

### Sheet: Expenses

| Column | Type | Description |
|--------|------|-------------|
| Date | DateTime | YYYY-MM-DD HH:MM |
| Category | String | rent/salary/utilities/materials/other |
| Amount | Number | Numeric amount (sum) |
| Description | String | Free text |
| Added_By | String | Admin's first name |

---

## 8. Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | From @BotFather |
| `WEBHOOK_URL` | ✅ | Public HTTPS URL + `/webhook` |
| `MINI_APP_URL` | ✅ | Public HTTPS URL of the Mini App |
| `GOOGLE_SPREADSHEET_ID` | ✅ | From Sheets URL |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ✅* | Full JSON as string |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | ✅* | Path to JSON file (local alt) |
| `ADMIN_IDS` | ✅ | Comma-separated Telegram IDs |
| `TEACHER_IDS` | ✅ | Comma-separated Telegram IDs |
| `DEV_MODE` | ❌ | `true` bypasses auth signature |
| `PORT` | ❌ | Server port (default 8000) |

*One of `GOOGLE_SERVICE_ACCOUNT_JSON` or `GOOGLE_SERVICE_ACCOUNT_FILE` required.

---

## 9. Role System

| Role | Groups | Attendance | Homeworks | Expenses | Registration |
|------|--------|------------|-----------|----------|--------------|
| **Admin** | View + Create | Mark | Send | View + Add | Auto |
| **Teacher** | View | Mark | Send | — | Auto |
| **Student** | — | — | Receive via bot | — | Via bot /start |

**Assigning roles:**
- Set `ADMIN_IDS` and `TEACHER_IDS` environment variables
- Multiple IDs separated by commas: `ADMIN_IDS=123,456`
- Anyone not in those lists who starts the bot becomes a Student
- Admins and Teachers see the Mini App button when they send `/start`

---

## 10. API Reference

All endpoints require `X-Telegram-Init-Data` header (or `X-Telegram-ID` in dev mode).

### Auth
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/verify` | Verify session, returns role |

### Groups
| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/groups/` | all | List all groups |
| POST | `/api/groups/` | admin | Create group |
| GET | `/api/groups/{name}/students` | admin, teacher | Students in group |

### Attendance
| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/attendance/` | admin, teacher | Get records (filter: `?group=&date=`) |
| POST | `/api/attendance/` | admin, teacher | Submit attendance |

### Homeworks
| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/homeworks/` | admin, teacher | Get homework history |
| POST | `/api/homeworks/send` | admin, teacher | Send homework + Telegram delivery |

### Expenses
| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/expenses/` | admin | List all expenses + total |
| POST | `/api/expenses/` | admin | Add expense |

### Students
| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/students/` | admin, teacher | All students |
| GET | `/api/students/me` | all | Own profile |

### Webhook
| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhook/telegram` | Receives all Telegram updates |

---

## 11. Troubleshooting

### Bot doesn't respond
- Check `TELEGRAM_BOT_TOKEN` is correct
- Verify webhook: `https://api.telegram.org/bot{TOKEN}/getWebhookInfo`
- Check server logs for errors

### Google Sheets errors
- Ensure the service account email has **Editor** access to the spreadsheet
- Verify `GOOGLE_SPREADSHEET_ID` is correct (not the full URL)
- Check that both Sheets API and Drive API are enabled in Google Cloud Console

### Mini App doesn't open
- The URL in BotFather must be HTTPS (not HTTP)
- `MINI_APP_URL` must be publicly accessible
- Check browser console for CORS or API errors

### Homework not delivered
- Student must have started the bot (`/start`) to get a `Telegram_ID`
- Verify student's `Telegram_ID` column is not empty in the sheet
- Bot cannot initiate conversation unless user has previously messaged it

### Attendance duplicate error
- Attendance for a group+date combination can only be submitted once
- Check the Attendance sheet for existing entries

### Sheets not auto-created
- The app creates sheets on startup via `ensure_sheets_exist()`
- Check server startup logs
- Ensure service account has write access

---

## 12. Scaling & Migration

The backend uses a **Data Access Layer** pattern via `SheetsService`. To migrate to PostgreSQL:

1. Create `services/postgres.py` implementing the same public methods as `SheetsService`
2. Update `main.py` to import `PostgresService` instead of `SheetsService`
3. No changes needed in routers or bot logic

**Methods to implement for migration:**
```python
get_all_students()
get_student_by_telegram_id(telegram_id)
add_student(name, phone, telegram_id, group)
get_students_by_group(group_name)
get_all_groups()
add_group(group_name, teacher)
get_attendance(group, date)
save_attendance(date, group, attendance_list)
get_homeworks(group)
save_homework(group, homework_text, sent_by)
get_expenses()
add_expense(category, amount, description, added_by)
get_user_role(telegram_id)
```

For **Redis-backed conversation state** (multi-instance deployment), replace the `_conversation_state` dict in `webhook.py` with Redis calls.
