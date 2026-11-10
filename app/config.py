"""Environment-only configuration with safe defaults and secret-free hashes."""
import hashlib
import json
import os
from pathlib import Path
from typing import Literal
from pydantic import Field, SecretStr, model_validator
from app.contracts.common import StrictModel

class Settings(StrictModel):
    config_version: Literal["1.0"] = "1.0"
    environment: Literal["local", "test", "demo"] = "local"
    publishing_enabled: Literal[False] = False
    allow_paid_providers: bool = False
    model_provider: Literal["ollama", "api"] | None = None
    fake_stage_enabled: bool = False
    data_dir: Path = Path("data")
    github_client_secret: SecretStr | None = Field(default=None, repr=False, exclude=True)

    @model_validator(mode="after")
    def policy_defaults(self):
        if self.fake_stage_enabled and self.environment not in {"demo", "test"}:
            raise ValueError("fake stages require demo or test environment")
        if self.model_provider == "api" and not self.allow_paid_providers:
            raise ValueError("API providers require explicit paid-provider opt-in")
        return self

    @classmethod
    def from_env(cls) -> "Settings":
        values = {}
        boolean_fields = {"publishing_enabled", "allow_paid_providers", "fake_stage_enabled"}
        for name in cls.model_fields:
            raw = os.environ.get("FINANCE_" + name.upper())
            if raw is None:
                continue
            if name in boolean_fields:
                if raw.lower() not in {"true", "false"}:
                    raise ValueError("configuration boolean must be true or false")
                values[name] = raw.lower() == "true"
            elif name == "data_dir":
                values[name] = Path(raw)
            elif name == "github_client_secret":
                values[name] = SecretStr(raw)
            else:
                values[name] = raw
        return cls(**values)

    def config_hash(self) -> str:
        raw = json.dumps(self.model_dump(mode="json"),sort_keys=True,separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()
