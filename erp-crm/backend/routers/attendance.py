from datetime import date as Date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.sheets import SheetsService
from services.auth import get_current_user

router = APIRouter()


class AttendanceEntry(BaseModel):
    student_id: str
    student_name: str
    status: str  # "Present" | "Absent"


class SubmitAttendanceRequest(BaseModel):
    group: str
    date: str | None = None  # defaults to today
    attendance: list[AttendanceEntry]


@router.get("/")
async def get_attendance(
    group: str | None = None,
    date: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    sheets = SheetsService()
    try:
        records = sheets.get_attendance(group=group, date=date)
        return {"records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch attendance: {e}")


@router.post("/")
async def submit_attendance(
    body: SubmitAttendanceRequest,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") not in ("admin", "teacher"):
        raise HTTPException(status_code=403, detail="Only teachers and admins can submit attendance.")

    sheets = SheetsService()
    attendance_date = body.date or str(Date.today())

    try:
        count = sheets.save_attendance(
            date=attendance_date,
            group=body.group,
            attendance_list=[a.dict() for a in body.attendance],
        )
        return {"message": f"Attendance saved for {body.group} on {attendance_date}", "rows": count}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save attendance: {e}")
