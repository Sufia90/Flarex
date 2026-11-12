from pathlib import Path
from app.core.config import Settings, get_settings


def test_default_settings():
    s = Settings()
    assert s.app_name == "NASA Combustion Research Explorer"
    assert s.app_version == "0.2.0"
    assert s.app_env == "development"
    assert s.api_host == "127.0.0.1"
    assert s.api_port == 8000
    assert s.api_prefix == "/api"
    assert s.log_level == "INFO"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("APP_NAME", "Test Explorer")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("DEBUG", "true")
    s = Settings()
    assert s.app_name == "Test Explorer"
    assert s.app_env == "testing"
    assert s.api_port == 9000
    assert s.debug is True


def test_api_base_url():
    assert Settings().api_base_url == "http://127.0.0.1:8000"


def test_is_production():
    assert Settings(app_env="development").is_production is False
    assert Settings(app_env="production").is_production is True


def test_data_and_media_paths():
    s = Settings()
    assert isinstance(s.data_path, Path)
    assert isinstance(s.media_path, Path)


def test_get_settings_cached():
    get_settings.cache_clear()
    assert get_settings() is get_settings()


def test_cors_origins_default():
    assert Settings().cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_cors_origins_from_env(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://example.com", "http://localhost:3000"]')

    assert Settings().cors_origins == ["https://example.com", "http://localhost:3000"]
