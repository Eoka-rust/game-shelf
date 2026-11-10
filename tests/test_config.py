from config import Settings


def make_settings() -> Settings:
    # _env_file=None: тест не зависит от локального .env
    return Settings(_env_file=None)


def test_settings_reads_database_url_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    assert make_settings().database_url == "postgresql://user:pass@localhost:5432/db"


def test_app_version_has_safe_default(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.delenv("APP_VERSION", raising=False)
    assert make_settings().app_version == "dev"
