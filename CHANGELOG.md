# Changelog

Формат — [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версии — [SemVer](https://semver.org/lang/ru/).

## [Unreleased]

## [1.1.0] - 2026-11-11

### Added

- Оценка игры от 1 до 10 (`rating`) в `POST /games` и `PATCH /games/{id}`;
  в ответах и на странице появилось поле оценки.
- Миграция `002_add_rating.sql`: `ALTER TABLE games ADD COLUMN IF NOT EXISTS rating SMALLINT`.
  Обратно совместима — столбец nullable, код v1.0.0 продолжает работать.
- Тесты на оценку: сохранение, изменение, отказ при значении вне 1..10.

### Changed

- `GameRepo` и ответы API перечисляют `rating` явно; существующие строки получают `NULL`.

## [1.0.0] - 2026-11-10

### Added

- Сервис «Полка игр»: FastAPI + PostgreSQL, страница `static/index.html`.
- Эндпоинты `GET /`, `GET /health`, `GET /version`, `GET /games`, `POST /games`,
  `PATCH /games/{id}`.
- Схема `games` (`migrations/001_init.sql`), применение миграций при старте.
- Настройки на pydantic-settings, секреты через `.env`, в репозитории `.env.example`.
- Dockerfile с зависимостями отдельным слоем, `compose.yaml` (app + db, healthcheck,
  volume, пароль из `${...}`).
- CI: Ruff и pytest на push и pull_request, service-контейнер postgres для теста миграций.
- CD: публикация образа в ghcr.io после зелёного CI, только из `main`.
- Release: тег `vX.Y.Z` публикует образ с версией.
- README.md и RUNBOOK.md.

[Unreleased]: https://github.com/USERNAME/game-shelf/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/USERNAME/game-shelf/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/USERNAME/game-shelf/releases/tag/v1.0.0
