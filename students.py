from fastapi import APIRouter, Depends, HTTPException
from services.sheets import SheetsService
from services.auth import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Returns current user's profile and role."""
    sheets = SheetsService()
    telegram_id = str(current_user.get("id", ""))
    student = sheets.get_student_by_telegram_id(telegram_id)
    return {
        "telegram_user": current_user,
        "role": current_user.get("role"),
        "student_profile": student,
    }


@router.get("/")
async def list_students(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ("admin", "teacher"):
        raise HTTPException(status_code=403, detail="Access denied.")
    sheets = SheetsService()
    try:
        students = sheets.get_all_students()
        return {"students": students, "count": len(students)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch students: {e}")
