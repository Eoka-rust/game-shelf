from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from config import settings

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def apply_migrations() -> list[str]:
    """Применяет ещё не применённые .sql из migrations/ по возрастанию имени.

    Каждый файл выполняется один раз: имя записывается в schema_migrations.
    Повторный запуск (рестарт контейнера) ничего не делает — см. RUNBOOK.
    """
    applied: list[str] = []

    async with await psycopg.AsyncConnection.connect(settings.database_url) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    name TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            await cur.execute("SELECT name FROM schema_migrations")
            done = {row[0] for row in await cur.fetchall()}

            for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
                if path.name in done:
                    continue
                await cur.execute(path.read_text(encoding="utf-8"))
                await cur.execute(
                    "INSERT INTO schema_migrations (name) VALUES (%s)",
                    (path.name,),
                )
                applied.append(path.name)

        await conn.commit()

    return applied


class GameRepo:
    """Доступ к таблице games. В тестах подменяется заглушкой через Depends."""

    _SELECT = "SELECT id, title, platform, status FROM games"

    def __init__(self, conn: psycopg.AsyncConnection) -> None:
        self.conn = conn

    async def list_games(self, status: str | None = None) -> list[dict[str, Any]]:
        async with self.conn.cursor(row_factory=dict_row) as cur:
            if status is None:
                await cur.execute(f"{self._SELECT} ORDER BY id DESC")
            else:
                await cur.execute(
                    f"{self._SELECT} WHERE status = %s ORDER BY id DESC",
                    (status,),
                )
            return await cur.fetchall()

    async def add_game(self, title: str, platform: str, status: str) -> dict[str, Any]:
        async with self.conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                INSERT INTO games (title, platform, status)
                VALUES (%s, %s, %s)
                RETURNING id, title, platform, status
                """,
                (title, platform, status),
            )
            row = await cur.fetchone()
        await self.conn.commit()
        return row

    async def update_game(self, game_id: int, status: str | None = None) -> dict[str, Any] | None:
        async with self.conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                UPDATE games
                SET status = COALESCE(%s, status)
                WHERE id = %s
                RETURNING id, title, platform, status
                """,
                (status, game_id),
            )
            row = await cur.fetchone()
        await self.conn.commit()
        return row


async def get_repo() -> AsyncIterator[GameRepo]:
    async with await psycopg.AsyncConnection.connect(settings.database_url) as conn:
        yield GameRepo(conn)
