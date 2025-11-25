import logging
from colorlog import ColoredFormatter
from fastapi import FastAPI
from src.db.database import engine, Base
import uvicorn
from contextlib import asynccontextmanager
from src.endpoints.team import router as team_router
from src.endpoints.user import router as users_router
from src.endpoints.pull_request import router as pr_router
from src.endpoints.stats import router as stats_router


handler = logging.StreamHandler()
formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(lifespan=lifespan)
app.include_router(team_router)
app.include_router(users_router)
app.include_router(pr_router)
app.include_router(stats_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
