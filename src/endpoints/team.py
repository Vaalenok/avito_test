import json
from fastapi import HTTPException, status, Response, APIRouter
from pydantic import BaseModel
from typing import List
import src.db.crud as crud
from src.db.models import Team, User


router = APIRouter(prefix="/team")


class TeamMemberSchema(BaseModel):
    user_id: str
    username: str
    is_active: bool


class TeamSchema(BaseModel):
    team_name: str
    members: List[TeamMemberSchema]


@router.post("/add")
async def create_team(team: TeamSchema):
    db_team = await crud.get_by_param(Team, name=team.team_name)

    if db_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "TEAM_EXISTS", "message": "team_name already exists"}
            },
        )

    new_team = Team(name=team.team_name, members=[])
    db_team = await crud.create(new_team)

    for member in team.members:
        db_member = await crud.get(User, member.user_id)

        if db_member:
            if db_member in db_team.members or db_member.team_id:
                continue

        db_member = User(name=member.username, is_active=member.is_active)
        db_team.members.append(db_member)

    await crud.update(db_team)
    db_team = await crud.get_by_param(Team, name=team.team_name)

    return Response(
        content=json.dumps(
            {
                "team": {
                    "team_name": team.team_name,
                    "members": [
                        {
                            "user_id": str(member.id),
                            "username": member.name,
                            "is_active": member.is_active,
                        }
                        for member in db_team.members
                    ],
                }
            }
        ),
        status_code=status.HTTP_201_CREATED,
        media_type="application/json",
    )


@router.get("/get")
async def get_team(team_name: str):
    db_team = await crud.get_by_param(Team, name=team_name)

    if db_team:
        return {
            "name": db_team.name,
            "members": [
                {
                    "user_id": str(member.id),
                    "username": member.name,
                    "is_active": member.is_active,
                }
                for member in db_team.members
            ],
        }

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
