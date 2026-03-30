from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.sheets import SheetsService
from services.bot import BotService
from services.auth import get_current_user

router = APIRouter()


class SendHomeworkRequest(BaseModel):
    group: str
    homework_text: str


@router.get("/")
async def get_homeworks(
    group: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    sheets = SheetsService()
    try:
        records = sheets.get_homeworks(group=group)
        return {"homeworks": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch homeworks: {e}")


@router.post("/send")
async def send_homework(
    body: SendHomeworkRequest,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") not in ("admin", "teacher"):
        raise HTTPException(status_code=403, detail="Only teachers and admins can send homework.")

    sheets = SheetsService()
    bot = BotService()

    # Get students in the group
    students = sheets.get_students_by_group(body.group)
    if not students:
        raise HTTPException(status_code=404, detail=f"No students found in group '{body.group}'.")

    teacher_name = current_user.get("first_name", "Teacher")

    # Save to Sheets first
    try:
        sheets.save_homework(
            group=body.group,
            homework_text=body.homework_text,
            sent_by=teacher_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save homework: {e}")

    # Send via Telegram bot
    delivery = await bot.send_homework_to_group(
        students=students,
        group_name=body.group,
        homework_text=body.homework_text,
        teacher_name=teacher_name,
    )

    return {
        "message": "Homework sent",
        "group": body.group,
        "delivery": delivery,
        "total_students": len(students),
    }
