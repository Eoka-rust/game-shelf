import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

import main  # noqa: E402
from db import get_repo  # noqa: E402


class FakeRepo:
    """Заглушка GameRepo: те же три метода, но данные в памяти."""

    def __init__(self) -> None:
        self.games: list[dict] = []
        self.next_id = 1

    async def list_games(self, status: str | None = None) -> list[dict]:
        games = self.games
        if status is not None:
            games = [game for game in games if game["status"] == status]
        return list(reversed(games))

    async def add_game(self, title: str, platform: str, status: str) -> dict:
        game = {"id": self.next_id, "title": title, "platform": platform, "status": status}
        self.next_id += 1
        self.games.append(game)
        return game

    async def update_game(self, game_id: int, status: str | None = None) -> dict | None:
        for game in self.games:
            if game["id"] == game_id:
                if status is not None:
                    game["status"] = status
                return game
        return None


@pytest.fixture
def repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def client(repo: FakeRepo):
    async def override_get_repo():
        yield repo

    main.app.dependency_overrides[get_repo] = override_get_repo
    # Без `with конструктор` не запускает lifespan, поэтому база не нужна
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()
