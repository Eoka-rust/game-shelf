# RUNBOOK — «Полка игр»

Аварийная инструкция: что проверить, что написать в чат и как вернуть сервис.
Все команды выполняются на сервере из каталога с `compose.yaml` и `.env`.

## Как устроен выкат (чтобы понимать, что откатывать)

- Образы лежат в `ghcr.io/eoka-rust/game-shelf`, теги: `latest`, `sha-…` (из main) и `X.Y.Z` (релизы).
- На сервере `docker compose` берёт образ по переменной `APP_VERSION` из `.env`.
- Схема БД меняется только вперёд, при старте контейнера (`migrations/*.sql`), и только
  обратно совместимыми шагами. Назад миграции не откатываются.
- Данные — в volume `pgdata`. `docker compose down` их не удаляет; `down -v` удаляет.

## Первые 60 секунд

```bash
cd <каталог сервиса>
docker compose ps                 # кто не healthy
docker compose logs --tail=100 app
curl -sS localhost:8000/health    # {"status":"ok"}
curl -sS localhost:8000/version   # какая версия реально работает
```

## Симптом → действие

### 1. Страница не открывается, контейнер app перезапускается

```bash
docker compose logs --tail=200 app
```

- `Connection refused` / `could not connect to server` — база ещё поднимается или упала:
  `docker compose ps db`, `docker compose logs --tail=100 db`.
- `password authentication failed` — в `.env` сменили пароль, но volume `pgdata` создан со
  старым: вернуть прежний `POSTGRES_PASSWORD` или пересоздать базу (см. §5, это потеря данных).
- `relation "games" does not exist` — миграции не применились: посмотреть лог выше,
  проверить `SELECT * FROM schema_migrations;`.

### 2. `docker compose ps` показывает `unhealthy` у app

Healthcheck бьёт `/health`. Проверьте вручную:

```bash
docker compose exec app python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read())"
```

Если внутри контейнера 200, а снаружи нет — проблема в порту/прокси, а не в приложении.

### 3. После выката новой версии всё сломалось — ОТКАТ

```bash
# 1) какой тег был до этого
docker inspect --format '{{index .Config.Labels "org.opencontainers.image.version"}}' $(docker compose ps -q app)

# 2) подставить предыдущий релиз в .env
#    APP_VERSION=1.0.0

# 3) скачать именно этот образ и поднять сервис без пересборки
docker compose pull app
docker compose up -d --no-build app

# 4) убедиться
docker compose ps
curl -sS localhost:8000/version
curl -sS localhost:8000/health
```

Ожидаемо: `/version` показывает `v1.0.0`, `/health` — `ok`, существующие игры на месте.
Если `pull` отвечает `denied` — сначала `docker login ghcr.io` под аккаунтом с доступом к пакету.

Откат допустим, потому что схема меняется только обратно совместимыми шагами (см. README,
раздел «Почему миграция 002 обратно совместима»): старая версия работает на новой схеме.

### 4. Откат не помог или база недоступна

```bash
docker compose ps
docker compose logs --tail=200 db
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select count(*) from games;"
```

Если база не поднимается (повреждён volume, кончилось место):

```bash
docker system df        # свободное место
df -h
```

### 5. Восстановление базы из дампа

```bash
# бэкап делается заранее и хранится вне сервера
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup-$(date +%F).sql

# восстановление
docker compose stop app
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < backup-2026-11-11.sql
docker compose start app
```

Полное пересоздание (данные теряются):

```bash
docker compose down -v
docker compose up -d
```

### 6. Красный CI — образ не публикуется

- Смотреть лог job `check`: `Ruff …` → `uv run ruff check . --fix` локально и закоммитить;
  `pytest …` → `uv run pytest -q` локально.
- `build` пропущен, если упал `check` — это нормально, исправляем и пушим снова.
- `build` не запускается в PR — это тоже нормально, публикация только из `main`.

### 7. Тег поставили не туда

```bash
git tag -d v1.1.0                 # локально
git push origin :refs/tags/v1.1.0 # удалить на GitHub
# исправить коммит/версию и поставить тег заново
```

Образ с неудачным тегом останется в Packages — удалить вручную в веб-интерфейсе пакета.

## Чек-лист дежурного

1. `docker compose ps` — все `healthy`.
2. `curl /health` — `{"status":"ok"}`.
3. `curl /version` — совпадает с ожидаемым релизом.
4. В логах нет `Traceback`.
5. Если что-то из этого не так — откат по §3, потом разбор.

## Что приложить к сообщению об инциденте

- время обнаружения и версия из `/version`;
- вывод `docker compose ps`;
- последние 100 строк `docker compose logs app`;
- что уже пробовали (откат/рестарт) и результат.
