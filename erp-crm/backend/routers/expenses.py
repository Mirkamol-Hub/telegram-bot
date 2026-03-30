from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.sheets import SheetsService
from services.auth import get_current_user

router = APIRouter()

VALID_CATEGORIES = {"rent", "salary", "utilities", "materials", "other"}


class AddExpenseRequest(BaseModel):
    category: str
    amount: float
    description: str


@router.get("/")
async def get_expenses(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view expenses.")
    sheets = SheetsService()
    try:
        records = sheets.get_expenses()
        total = sum(float(r.get("Amount", 0)) for r in records)
        return {"expenses": records, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch expenses: {e}")


@router.post("/")
async def add_expense(
    body: AddExpenseRequest,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can add expenses.")
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Choose from: {VALID_CATEGORIES}")
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive.")

    sheets = SheetsService()
    added_by = current_user.get("first_name", "Admin")
    try:
        expense = sheets.add_expense(body.category, body.amount, body.description, added_by)
        return {"message": "Expense recorded", "expense": expense}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add expense: {e}")
