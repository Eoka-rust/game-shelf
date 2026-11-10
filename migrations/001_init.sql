-- 001: базовая схема «Полки игр» (релиз 1.0.0)
-- Файлы применяются по порядку имён, по одному разу (см. schema_migrations в db.py).

CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'backlog',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS games_status_idx ON games (status);
