import datetime
import uuid
import pytz
from sqlalchemy import ForeignKey, Enum as SQLEnum, Table, Column
from sqlalchemy.orm import Mapped, MappedColumn, relationship
from src.db.database import Base
from enum import Enum
from src.config import TIME_ZONE


def now():
    return datetime.datetime.now(pytz.timezone(TIME_ZONE)).replace(tzinfo=None)


class PRStatus(str, Enum):
    OPEN = "OPEN"
    MERGED = "MERGED"


reviewers_association = Table(
    "reviewers_association",
    Base.metadata,
    Column(
        "pr_id", ForeignKey("pull_requests.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    name: Mapped[str] = MappedColumn()
    team: Mapped["Team"] = relationship(
        "Team", back_populates="members", lazy="selectin"
    )
    pull_requests: Mapped[list["PullRequest"]] = relationship(
        "PullRequest",
        back_populates="author",
        cascade="save-update, merge",
        lazy="selectin",
    )
    reviewed_prs: Mapped[list["PullRequest"]] = relationship(
        "PullRequest",
        secondary=reviewers_association,
        back_populates="reviewers",
        cascade="save-update, merge",
        lazy="selectin",
    )
    is_active: Mapped["bool"] = MappedColumn(default=True)

    team_id: Mapped[uuid.UUID | None] = MappedColumn(
        ForeignKey("teams.id", ondelete="SET NULL")
    )


class Team(Base):
    __tablename__ = "teams"

    name: Mapped[str] = MappedColumn(unique=True)
    members: Mapped[list["User"]] = relationship(
        "User",
        back_populates="team",
        cascade="save-update, merge",
        passive_deletes=True,
        lazy="selectin",
    )


class PullRequest(Base):
    __tablename__ = "pull_requests"

    name: Mapped[str] = MappedColumn()
    author: Mapped["User"] = relationship(
        "User", back_populates="pull_requests", lazy="selectin"
    )
    status: Mapped[PRStatus] = MappedColumn(SQLEnum(PRStatus), default=PRStatus.OPEN)
    reviewers: Mapped[list["User"]] = relationship(
        "User",
        secondary=reviewers_association,
        back_populates="reviewed_prs",
        cascade="save-update, merge",
        lazy="selectin",
    )
    created_at: Mapped[datetime.datetime | None] = MappedColumn(default=now())
    merged_at: Mapped[datetime.datetime | None] = MappedColumn(default=now())

    author_id: Mapped[uuid.UUID] = MappedColumn(
        ForeignKey("users.id", ondelete="CASCADE")
    )
