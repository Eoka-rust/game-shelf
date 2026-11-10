"""Тест на реальной базе: включается, только если задан TEST_DATABASE_URL.

В CI переменная приходит из service-контейнера postgres, локально тест пропускается.
"""

import asyncio
import os

import psycopg
import pytest

from config import settings
from db import apply_migrations

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL не задан — тест на реальной базе пропущен",
)


def test_migrations_apply_and_are_idempotent(monkeypatch):
    monkeypatch.setattr(settings, "database_url", TEST_DATABASE_URL)

    first_run = asyncio.run(apply_migrations())
    second_run = asyncio.run(apply_migrations())

    assert "001_init.sql" in first_run
    assert second_run == [], "повторный запуск не должен применять миграции заново"

    with psycopg.connect(TEST_DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO games (title, platform) VALUES ('Hades', 'PC') RETURNING id")
        game_id = cur.fetchone()[0]
        cur.execute("SELECT status FROM games WHERE id = %s", (game_id,))
        assert cur.fetchone()[0] == "backlog"
        conn.rollback()
