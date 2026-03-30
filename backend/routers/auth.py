from fastapi import APIRouter, Depends
from services.auth import get_current_user

router = APIRouter()


@router.get("/verify")
async def verify(current_user: dict = Depends(get_current_user)):
    """Verify token and return role — called by Mini App on load."""
    return {
        "ok": True,
        "user": {
            "id": current_user.get("id"),
            "first_name": current_user.get("first_name"),
            "username": current_user.get("username"),
            "role": current_user.get("role"),
        }
    }
