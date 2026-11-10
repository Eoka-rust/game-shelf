-- 002: оценка игры (релиз 1.1.0)
-- Обратно совместимо: столбец допускает NULL, без NOT NULL и без DEFAULT.
-- Код v1.0.0 не знает про rating и перечисляет столбцы явно, поэтому продолжает
-- работать и на этой схеме. Старые строки получают rating = NULL.

ALTER TABLE games ADD COLUMN IF NOT EXISTS rating SMALLINT;

COMMENT ON COLUMN games.rating IS 'Оценка 1..10, NULL — игра ещё не оценена. Добавлено в 1.1.0';
