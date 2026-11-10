from config import Settings


def test_settings_reads_database_url_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    settings = Settings()
    assert settings.database_url == "postgresql://user:pass@localhost:5432/db"


def test_app_version_has_safe_default(monkeypatch):
    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    assert Settings().app_version == "dev"
