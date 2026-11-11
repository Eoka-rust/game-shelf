# Changelog

Формат — [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версии — [SemVer](https://semver.org/lang/ru/).

## [Unreleased]

## [1.2.3] - 2026-11-11

### Fixed

- На телефоне карточка игры растягивалась на пустую высоту: во flex-колонке
  `flex: 1 1 200px` у `.game__info` работал как высота. Заменено на `flex: 0 0 auto`,
  у карточки `justify-content: flex-start`.

## [1.2.2] - 2026-11-11

### Fixed

- Текст в селектах «В очередь» и «Без оценки» упирался в стрелку: добавлен
  `padding-right` под нативный caret, ширина страницы увеличена до 860px,
  колонки формы перераспределены (`1.8fr / 1fr / 1.15fr / 145px / auto`).

## [1.2.1] - 2026-11-11

### Fixed

- Кнопка «Добавить» выходила за границу карточки формы: колонки grid не могли
  сжаться ниже внутренней ширины полей. Исправлено `minmax(0, …)`,
  `min-width: 0` и `width: 100%` у полей, `white-space: nowrap` у кнопки.

### Changed

- Все стили вынесены из `index.html` в `static/style.css` и отдаются по `/static/style.css`.
- Адаптивная вёрстка: 2 колонки до 900px, 1 колонка до 560px, карточки игр
  в столбик на телефоне, размер интерактивных элементов от 44px.
- Тесты: страница подключает внешний CSS, `/static/style.css` отдаётся с `text/css`.

## [1.2.0] - 2026-11-11

### Added

- `DELETE /games/{id}` — удаление игры, `204` при успехе и `404`, если игры нет.
- Кнопка «Удалить» в списке на странице; удаление с подтверждением.

### Note

- Изменений схемы нет: удаление — обычный `DELETE` по `id`, откат на 1.1.0 к той же
  базе безопасен.

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

[Unreleased]: https://github.com/eoka-rust/game-shelf/compare/v1.2.3...HEAD
[1.2.3]: https://github.com/eoka-rust/game-shelf/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/eoka-rust/game-shelf/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/eoka-rust/game-shelf/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/eoka-rust/game-shelf/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/eoka-rust/game-shelf/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/eoka-rust/game-shelf/releases/tag/v1.0.0
