# Полка игр

Мини-сервис: список игр с платформой и статусом (в очереди / играю / пройдена).
FastAPI + PostgreSQL, одна HTML-страница, четыре эндпоинта. Всё упаковано в Docker и
доведено до прода: CI, публикация образа в ghcr.io, релизы по semver-тегам и откат.

```
[Браузер] → FastAPI (app) → PostgreSQL (db)
```

## Что умеет

| Метод | Путь | Что делает |
|-------|------|------------|
| GET | `/` | HTML-страница «Полка игр» |
| GET | `/health` | проверка живости (её использует healthcheck в compose) |
| GET | `/version` | версия образа, попавшая в сборку |
| GET | `/games` | список игр, фильтр `?status=backlog\|playing\|completed` |
| POST | `/games` | добавить игру: `{"title": "...", "platform": "...", "status": "backlog", "rating": 9}` (оценка 1..10 или `null`) |
| PATCH | `/games/{id}` | сменить статус и/или оценку: `{"status": "playing", "rating": 8}` |
| DELETE | `/games/{id}` | удалить игру, ответ `204` (404 — если игры нет) |

Swagger: `http://localhost:8000/docs`.

## Быстрый старт

```bash
cp .env.example .env          # поменяйте пароль и IMAGE_NAME под свой логин GitHub
docker compose up -d --build
curl http://localhost:8000/health
```

Открыть `http://localhost:8000` — форма добавления и список игр.
Остановить: `docker compose down`. Данные лежат в volume `pgdata` и переживают `down`/`up`
(удалить вместе с данными — `docker compose down -v`).

### Локально без Docker

```bash
uv sync
# в .env: DATABASE_URL=postgresql://gameshelf:<пароль>@localhost:5432/gameshelf
docker compose up -d db        # только база
uv run uvicorn main:app --reload
```

### Проверки

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

Тест на реальной базе включается переменной `TEST_DATABASE_URL` (в CI она приходит из
service-контейнера postgres); локально без неё он пропускается.

## Структура

```
main.py               FastAPI: эндпоинты, схемы запросов/ответов, lifespan
config.py             настройки (pydantic-settings), всё из env/.env
db.py                 миграции и GameRepo — единственное место с SQL
migrations/           001_init.sql, 002_add_rating.sql — по файлу на изменение схемы
static/index.html     страница: fetch к /games и /version
tests/                pytest: API на заглушке репозитория + тест миграций на живой БД
compose.yaml          app + db, healthcheck, volume, пароль из ${...}
Dockerfile            зависимости отдельным слоем, --host 0.0.0.0
.github/workflows/    ci.yml (check → build), release.yml (тег vX.Y.Z)
RUNBOOK.md            что делать, когда всё сломалось и как откатиться
CHANGELOG.md          история версий
```

## Настройки

Все настройки собраны в `config.py` на pydantic-settings. В коде нет ни адреса базы,
ни пароля; секретов нет в коммитах — только `.env.example`.

| Переменная | Где нужна | Значение |
|------------|-----------|----------|
| `DATABASE_URL` | app | строка подключения к PostgreSQL |
| `APP_VERSION` | app | версия, которую показывает `/version` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | db | реквизиты базы (пароль подставляет compose) |
| `IMAGE_NAME` | compose | `ghcr.io/eoka-rust/game-shelf` |

## CI/CD

`ci.yml` — на каждый **push** и **pull_request**:

1. `check` — Ruff (линтер + форматирование) и pytest; поднимается service-контейнер
   postgres, чтобы прогнать миграции на настоящей базе;
2. `build` — только если `check` зелёный (`needs: check`) и только для `main`:
   образ собирается и публикуется в `ghcr.io/eoka-rust/game-shelf` с тегами `latest` и `sha-…`.

`release.yml` — на тег вида `vX.Y.Z`:

1. проверяет, что тег совпадает с `version` в `pyproject.toml`;
2. собирает образ с `APP_VERSION=vX.Y.Z` и публикует теги `X.Y.Z` и `X.Y`.

Полный цикл релиза:

```bash
# 1. изменение в main → зелёный CI → в Packages появился :latest
# 2. поднять версию и записать изменения
#    pyproject.toml: version = "1.1.0"
#    CHANGELOG.md:   новый раздел
uv lock                       # обновить версию проекта в uv.lock
git commit -am "release: 1.1.0"
git tag -a v1.1.0 -m "1.1.0"
git push origin main --tags
```

## Почему миграция 002 обратно совместима

`002_add_rating.sql` добавляет только `rating SMALLINT NULL` — столбец, который может быть
пустым и не имеет `NOT NULL`/`DEFAULT`, требующего перезаписи строк. Отсюда:

- **старый код (v1.0.0) продолжает работать** на новой схеме: он перечисляет столбцы
  явно (`SELECT id, title, platform, status`) и не знает про `rating`;
- `INSERT` без `rating` проходит — значение `NULL` допустимо;
- `DROP`/переименований нет, старые запросы не ломаются.

Поэтому порядок выката безопасен в обе стороны: сначала миграция (она не мешает старой
версии), затем новый образ. Откат на v1.0.0 не требует откатывать схему — старый код
просто перестаёт читать новый столбец. Если бы столбец был `NOT NULL` без `DEFAULT`,
старый `INSERT` из v1.0.0 начал бы падать сразу после миграции — это и есть типичная
несовместимость.

## Откат

Коротко: `docker compose` берёт образ по `APP_VERSION`, поэтому откат — это запуск
предыдущего тега, без пересборки и без миграций назад. Полная процедура, диагностика и
аварийные сценарии — в [RUNBOOK.md](RUNBOOK.md).

## Демонстрация релиза

1. `git push` → вкладка Actions: зелёный `check`, затем `build`.
2. Packages: образ `:latest`.
3. `git tag -a v1.1.0` + push тега → Release: образ `1.1.0`.
4. Выкат `APP_VERSION=1.1.0`, затем откат `APP_VERSION=1.0.0` — `/version` показывает
   прежнюю версию, данные на месте.
