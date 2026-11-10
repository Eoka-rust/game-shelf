from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config import settings
from db import GameRepo, apply_migrations, get_repo

Status = Literal["backlog", "playing", "completed"]
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    applied = await apply_migrations()
    if applied:
        print(f"Применены миграции: {', '.join(applied)}", flush=True)
    yield


app = FastAPI(title="Полка игр", version=settings.app_version, lifespan=lifespan)


class GameIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    platform: str = Field(min_length=1, max_length=50)
    status: Status = "backlog"


class GamePatch(BaseModel):
    status: Status | None = None


class GameOut(BaseModel):
    id: int
    title: str
    platform: str
    status: str


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    return {"version": settings.app_version}


@app.get("/games", response_model=list[GameOut])
async def list_games(
    status: Status | None = None,
    repo: GameRepo = Depends(get_repo),
) -> list[dict]:
    return await repo.list_games(status)


@app.post("/games", response_model=GameOut, status_code=201)
async def add_game(game: GameIn, repo: GameRepo = Depends(get_repo)) -> dict:
    return await repo.add_game(game.title, game.platform, game.status)


@app.patch("/games/{game_id}", response_model=GameOut)
async def update_game(
    game_id: int,
    patch: GamePatch,
    repo: GameRepo = Depends(get_repo),
) -> dict:
    game = await repo.update_game(game_id, status=patch.status)
    if game is None:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    return game
