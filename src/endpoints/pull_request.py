import json
import random
from fastapi import HTTPException, APIRouter, Response, status as http_status
from pydantic import BaseModel
import src.db.crud as crud
from src.db.models import Team, User, PullRequest, now


router = APIRouter(prefix="/pullRequest")


class PullRequestSchema(BaseModel):
    pull_request_id: str
    pull_request_name: str
    author_id: str


class PullRequestIdSchema(BaseModel):
    pull_request_id: str


class PullRequestReassignSchema(BaseModel):
    pull_request_id: str
    old_user_id: str


@router.post("/create")
async def create_pull_request(pull_request: PullRequestSchema):
    db_pr = await crud.get(PullRequest, pull_request.pull_request_id)

    if db_pr:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail={"error": {"code": "PR_EXISTS", "message": "PR id already exists"}},
        )

    db_author = await crud.get(User, pull_request.author_id)
    db_author_team = await crud.get(Team, db_author.team.id)

    if not db_author:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND)

    potential_reviewers = [
        user
        for user in db_author_team.members
        if user.is_active and user.id != db_author.id
    ]

    if len(potential_reviewers) > 1:
        selected_reviewers = random.sample(potential_reviewers, 2)
    else:
        selected_reviewers = potential_reviewers

    new_pr = PullRequest(
        name=pull_request.pull_request_name,
        author_id=db_author.id,
        reviewers=selected_reviewers,
    )
    new_pr = await crud.create(new_pr)

    return Response(
        content=json.dumps(
            {
                "pr": {
                    "pull_request_id": str(pull_request.pull_request_id),
                    "pull_request_name": pull_request.pull_request_name,
                    "author_id": str(pull_request.author_id),
                    "status": new_pr.status,
                    "assigned_reviewers": [str(rev.id) for rev in new_pr.reviewers],
                }
            }
        ),
        status_code=http_status.HTTP_201_CREATED,
        media_type="application/json",
    )


@router.post("/merge")
async def merge_pull_request(data: PullRequestIdSchema):
    db_pr = await crud.get(PullRequest, data.pull_request_id)

    if not db_pr:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND)

    if db_pr.status == "OPEN":
        db_pr.status = "MERGED"
        db_pr.merged_at = now()
        await crud.update(db_pr)

    return {
        "pr": {
            "pull_request_id": data.pull_request_id,
            "pull_request_name": db_pr.name,
            "author_id": db_pr.author_id,
            "status": db_pr.status,
            "assigned_reviewers": [rev.id for rev in db_pr.reviewers],
            "mergedAt": db_pr.merged_at,
        }
    }


@router.post("/reassign")
async def reassign_pull_request(data: PullRequestReassignSchema):
    db_pr = await crud.get(PullRequest, data.pull_request_id)
    db_reviewer = await crud.get(User, data.old_user_id)

    if not db_pr or not db_reviewer:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND)

    if db_pr.status == "MERGED":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "PR_MERGED",
                    "message": "cannot reassign on merged PR",
                }
            },
        )

    if db_reviewer.id not in [user.id for user in db_pr.reviewers]:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "NOT_ASSIGNED",
                    "message": "reviewer is not assigned to this PR",
                }
            },
        )

    db_team = await crud.get(Team, db_reviewer.team.id)
    potential_reviewers = [
        user
        for user in db_team.members
        if user.is_active
        and user.id != db_reviewer.id
        and user.id != db_pr.author_id
        and user.id not in [user.id for user in db_pr.reviewers]
    ]

    if len(potential_reviewers) > 0:
        selected_reviewer = random.choice(potential_reviewers)
    else:
        selected_reviewer = None

    if not selected_reviewer:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "NO_CANDIDATE",
                    "message": "no active replacement candidate in team",
                }
            },
        )

    idx = next(
        (i for i, r in enumerate(db_pr.reviewers) if r.id == db_reviewer.id), None
    )
    db_pr.reviewers[idx] = selected_reviewer
    await crud.update(db_pr)

    return {
        "pr": {
            "pull_request_id": data.pull_request_id,
            "pull_request_name": db_pr.name,
            "author_id": db_pr.author_id,
            "status": db_pr.status,
            "assigned_reviewers": [rev.id for rev in db_pr.reviewers],
        },
        "replaced_by": selected_reviewer.id,
    }
