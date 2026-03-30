from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.sheets import SheetsService
from services.auth import get_current_user

router = APIRouter()


class CreateGroupRequest(BaseModel):
    group_name: str
    teacher: str


@router.get("/")
async def list_groups(current_user: dict = Depends(get_current_user)):
    sheets = SheetsService()
    try:
        groups = sheets.get_all_groups()
        return {"groups": groups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch groups: {e}")


@router.get("/{group_name}/students")
async def group_students(group_name: str, current_user: dict = Depends(get_current_user)):
    sheets = SheetsService()
    try:
        students = sheets.get_students_by_group(group_name)
        return {"group": group_name, "students": students, "count": len(students)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch students: {e}")


@router.post("/")
async def create_group(body: CreateGroupRequest, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create groups.")
    sheets = SheetsService()
    try:
        group = sheets.add_group(body.group_name, body.teacher)
        return {"message": "Group created", "group": group}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create group: {e}")
