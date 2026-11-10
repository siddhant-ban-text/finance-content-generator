import pytest
from pydantic import ValidationError
from app.config import Settings

def test_safe_config_defaults():
    settings=Settings.from_env()
    assert settings.publishing_enabled is False
    assert settings.allow_paid_providers is False
    assert settings.model_provider is None
    assert settings.fake_stage_enabled is False

def test_secrets_not_in_repr(monkeypatch):
    monkeypatch.setenv("FINANCE_GITHUB_CLIENT_SECRET","sentinel-local-secret")
    settings=Settings.from_env()
    assert "sentinel-local-secret" not in repr(settings)
    assert "sentinel-local-secret" not in settings.model_dump_json()
    first=settings.config_hash()
    monkeypatch.setenv("FINANCE_GITHUB_CLIENT_SECRET","different-local-secret")
    assert Settings.from_env().config_hash() == first

def test_fake_stage_requires_demo_or_test(monkeypatch):
    monkeypatch.setenv("FINANCE_FAKE_STAGE_ENABLED","true")
    with pytest.raises(ValidationError):
        Settings.from_env()
    monkeypatch.setenv("FINANCE_ENVIRONMENT","demo")
    assert Settings.from_env().fake_stage_enabled is True

def test_paid_provider_requires_optin(monkeypatch):
    monkeypatch.setenv("FINANCE_MODEL_PROVIDER","api")
    with pytest.raises(ValidationError):
        Settings.from_env()

def test_invalid_boolean_and_publish_activation_denied(monkeypatch):
    monkeypatch.setenv("FINANCE_ALLOW_PAID_PROVIDERS","maybe")
    with pytest.raises(ValueError):
        Settings.from_env()
    monkeypatch.delenv("FINANCE_ALLOW_PAID_PROVIDERS")
    monkeypatch.setenv("FINANCE_PUBLISHING_ENABLED","true")
    with pytest.raises(ValidationError):
        Settings.from_env()
