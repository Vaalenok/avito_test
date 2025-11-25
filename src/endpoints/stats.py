import uuid
from fastapi import HTTPException, APIRouter, status as http_status
import src.db.crud as crud
from src.db.models import User


router = APIRouter(prefix="/stats")


@router.get("/get")
async def get_stats(user_id: str | None, pull_request_id: str | None):
    if not user_id and not pull_request_id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST)

    db_user = await crud.get(User, uuid.UUID(user_id))

    if not db_user:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND)

    return {
        "user_stats": {
            "open_prs": len(
                [pr for pr in db_user.pull_requests if pr.status == "OPEN"]
            ),
            "merged_prs": len(
                [pr for pr in db_user.pull_requests if pr.status == "MERGED"]
            ),
            "reviewed_prs": len(db_user.reviewed_prs),
        }
    }
