"""
Google Sheets Data Access Layer
All sheet interactions go through this service.
Designed for easy migration to PostgreSQL/Firebase.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAMES = {
    "students":   "Students",
    "groups":     "Groups",
    "attendance": "Attendance",
    "homeworks":  "Homeworks",
    "expenses":   "Expenses",
}

SHEET_HEADERS = {
    "students":   ["Student_ID", "Name", "Phone", "Telegram_ID", "Group", "Join_Date"],
    "groups":     ["Group_ID", "Group_Name", "Teacher", "Student_Count"],
    "attendance": ["Date", "Group", "Student_ID", "Student_Name", "Status"],
    "homeworks":  ["Date", "Group", "Homework_Text", "Sent_By"],
    "expenses":   ["Date", "Category", "Amount", "Description", "Added_By"],
}


class SheetsService:
    """
    Central data access layer for Google Sheets.
    Replace _get_sheet() internals to migrate to another DB.
    """

    def __init__(self):
        self._client: Optional[gspread.Client] = None
        self._spreadsheet: Optional[gspread.Spreadsheet] = None
        self.spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID", "")

    def _get_client(self) -> gspread.Client:
        if self._client:
            return self._client
        creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if creds_json:
            info = json.loads(creds_json)
        else:
            creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
            with open(creds_file) as f:
                info = json.load(f)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        self._client = gspread.authorize(creds)
        return self._client

    def _get_spreadsheet(self) -> gspread.Spreadsheet:
        if self._spreadsheet:
            return self._spreadsheet
        client = self._get_client()
        self._spreadsheet = client.open_by_key(self.spreadsheet_id)
        return self._spreadsheet

    def _get_sheet(self, name: str) -> gspread.Worksheet:
        return self._get_spreadsheet().worksheet(SHEET_NAMES[name])

    # ── Schema management ────────────────────────────────────────────────────

    async def ensure_sheets_exist(self):
        """Create missing sheets and write headers if absent."""
        try:
            ss = self._get_spreadsheet()
            existing = {ws.title for ws in ss.worksheets()}
            for key, title in SHEET_NAMES.items():
                if title not in existing:
                    ws = ss.add_worksheet(title=title, rows=1000, cols=20)
                    ws.append_row(SHEET_HEADERS[key])
                    logger.info(f"Created sheet: {title}")
                else:
                    ws = ss.worksheet(title)
                    row1 = ws.row_values(1)
                    if not row1:
                        ws.append_row(SHEET_HEADERS[key])
        except Exception as e:
            logger.error(f"ensure_sheets_exist failed: {e}")

    # ── Generic helpers ──────────────────────────────────────────────────────

    def _rows_to_dicts(self, sheet_key: str) -> list[dict]:
        ws = self._get_sheet(sheet_key)
        records = ws.get_all_records()
        return records

    def _append_row(self, sheet_key: str, values: list):
        ws = self._get_sheet(sheet_key)
        ws.append_row(values, value_input_option="USER_ENTERED")

    # ── Students ─────────────────────────────────────────────────────────────

    def get_all_students(self) -> list[dict]:
        return self._rows_to_dicts("students")

    def get_student_by_telegram_id(self, telegram_id: str) -> Optional[dict]:
        students = self.get_all_students()
        for s in students:
            if str(s.get("Telegram_ID")) == str(telegram_id):
                return s
        return None

    def student_exists(self, telegram_id: str) -> bool:
        return self.get_student_by_telegram_id(telegram_id) is not None

    def add_student(self, name: str, phone: str, telegram_id: str, group: str) -> dict:
        students = self.get_all_students()
        # Duplicate check
        for s in students:
            if str(s.get("Telegram_ID")) == str(telegram_id):
                raise ValueError("Student already registered.")
        student_id = f"STU{len(students) + 1:04d}"
        join_date = datetime.now().strftime("%Y-%m-%d")
        self._append_row("students", [student_id, name, phone, str(telegram_id), group, join_date])
        self._update_group_count(group)
        return {"Student_ID": student_id, "Name": name, "Group": group}

    def get_students_by_group(self, group_name: str) -> list[dict]:
        return [s for s in self.get_all_students() if s.get("Group") == group_name]

    # ── Groups ───────────────────────────────────────────────────────────────

    def get_all_groups(self) -> list[dict]:
        return self._rows_to_dicts("groups")

    def get_group(self, group_name: str) -> Optional[dict]:
        for g in self.get_all_groups():
            if g.get("Group_Name") == group_name:
                return g
        return None

    def add_group(self, group_name: str, teacher: str) -> dict:
        groups = self.get_all_groups()
        for g in groups:
            if g.get("Group_Name") == group_name:
                raise ValueError("Group already exists.")
        group_id = f"GRP{len(groups) + 1:03d}"
        self._append_row("groups", [group_id, group_name, teacher, 0])
        return {"Group_ID": group_id, "Group_Name": group_name, "Teacher": teacher}

    def _update_group_count(self, group_name: str):
        """Recalculate and update Student_Count for a group."""
        try:
            ws = self._get_sheet("groups")
            records = ws.get_all_records()
            for i, row in enumerate(records, start=2):  # row 1 = header
                if row.get("Group_Name") == group_name:
                    count = len(self.get_students_by_group(group_name))
                    ws.update_cell(i, 4, count)
                    break
        except Exception as e:
            logger.warning(f"Could not update group count: {e}")

    # ── Attendance ───────────────────────────────────────────────────────────

    def get_attendance(self, group: Optional[str] = None, date: Optional[str] = None) -> list[dict]:
        records = self._rows_to_dicts("attendance")
        if group:
            records = [r for r in records if r.get("Group") == group]
        if date:
            records = [r for r in records if r.get("Date") == date]
        return records

    def attendance_exists(self, date: str, group: str) -> bool:
        records = self.get_attendance(group=group, date=date)
        return len(records) > 0

    def save_attendance(self, date: str, group: str, attendance_list: list[dict]) -> int:
        """
        attendance_list: [{"student_id": ..., "student_name": ..., "status": "Present"|"Absent"}]
        Returns number of rows saved.
        """
        if self.attendance_exists(date, group):
            raise ValueError(f"Attendance for {group} on {date} already submitted.")
        for item in attendance_list:
            self._append_row("attendance", [
                date,
                group,
                item["student_id"],
                item["student_name"],
                item["status"],
            ])
        return len(attendance_list)

    # ── Homeworks ────────────────────────────────────────────────────────────

    def get_homeworks(self, group: Optional[str] = None) -> list[dict]:
        records = self._rows_to_dicts("homeworks")
        if group:
            records = [r for r in records if r.get("Group") == group]
        return records

    def save_homework(self, group: str, homework_text: str, sent_by: str) -> dict:
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._append_row("homeworks", [date, group, homework_text, sent_by])
        return {"date": date, "group": group, "homework": homework_text, "sent_by": sent_by}

    # ── Expenses ─────────────────────────────────────────────────────────────

    def get_expenses(self) -> list[dict]:
        return self._rows_to_dicts("expenses")

    def add_expense(self, category: str, amount: float, description: str, added_by: str) -> dict:
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._append_row("expenses", [date, category, amount, description, added_by])
        return {"date": date, "category": category, "amount": amount, "description": description}

    # ── Roles / Auth ─────────────────────────────────────────────────────────

    def get_user_role(self, telegram_id: str) -> str:
        """
        Roles stored as env vars for simplicity.
        ADMIN_IDS=123,456  TEACHER_IDS=789,101
        """
        admin_ids = os.getenv("ADMIN_IDS", "").split(",")
        teacher_ids = os.getenv("TEACHER_IDS", "").split(",")
        if str(telegram_id) in admin_ids:
            return "admin"
        if str(telegram_id) in teacher_ids:
            return "teacher"
        return "student"
