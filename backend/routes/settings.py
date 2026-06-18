"""Settings and config endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
import yaml

router = APIRouter()


class LLMProviderInfo(BaseModel):
    name: str
    backend: str
    api_base: str | None = None
    model: str
    note: str
    api_key_env: str
    configured: bool


class Settings(BaseModel):
    providers: list[LLMProviderInfo]
    obsidian_vault: str
    default_backend: str


@router.get("", response_model=Settings)
def get_settings():
    """Return current settings and LLM provider presets."""
    import os

    with open("config/schedule.yaml") as f:
        cfg = yaml.safe_load(f)

    providers_cfg = cfg.get("llm_providers", {})
    providers: list[LLMProviderInfo] = []
    for name, p in providers_cfg.items():
        key_env = p.get("api_key_env", "")
        providers.append(
            LLMProviderInfo(
                name=name,
                backend=p.get("backend", "openai"),
                api_base=p.get("api_base"),
                model=p.get("model", ""),
                note=p.get("note", ""),
                api_key_env=key_env,
                configured=bool(os.environ.get(key_env)),
            )
        )

    return Settings(
        providers=providers,
        obsidian_vault=cfg.get("obsidian", {}).get("vault_path", ""),
        default_backend=cfg.get("llm", {}).get("default_backend", "manual"),
    )
