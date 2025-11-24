from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel
import src.db.crud as crud
from src.db.models import User


router = APIRouter(prefix="/users")


class UserActiveStatusSchema(BaseModel):
    user_id: str
    is_active: bool


@router.post("/setIsActive")
async def set_user_status(user: UserActiveStatusSchema):
    db_user = await crud.get(User, user.user_id)

    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    db_user.is_active = user.is_active
    await crud.update(db_user)

    return {
        "user": {
            "user_id": db_user.id,
            "username": db_user.name,
            "team_name": db_user.team.name,
            "is_active": db_user.is_active,
        }
    }


# TODO: отдебажить
@router.get("/getReview")
async def get_user_reviews(user_id: str):
    db_user = await crud.get(User, user_id)

    if db_user:
        return {
            "user_id": str(user_id),
            "pull_requests": [
                {
                    "pull_request_id": str(pr.id),
                    "pull_request_name": pr.name,
                    "author_id": pr.author_id,
                    "status": pr.status,
                }
                for pr in db_user.pull_requests
            ],
        }

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
