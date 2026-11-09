from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# UI 이름 → provider/model. 실제 키·URL은 secrets/환경변수.
# openai_compatible: OpenAI Chat Completions 형식 (Solar/OpenRouter/OpenAI/EXAONE)
MODELS: dict[str, dict[str, str]] = {
    "Solar": {
        "provider": "openai_compatible",
        "model": "solar-pro4",
        "label": "Upstage Solar",
        "base_url_default": "https://api.upstage.ai/v1",
        "key_env": "SOLAR_API_KEY",
        "model_env": "SOLAR_MODEL_ID",
        "url_env": "SOLAR_BASE_URL",
    },
    "Gemini": {
        "provider": "google",
        "model": "gemini-2.0-flash",
        "label": "Google Gemini",
        "base_url_default": "https://generativelanguage.googleapis.com/v1beta",
        "key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL_ID",
        "url_env": "GEMINI_BASE_URL",
    },
    "Llama": {
        "provider": "openai_compatible",
        "model": "meta-llama/llama-3.3-70b-instruct",
        "label": "Llama (OpenRouter)",
        "base_url_default": "https://openrouter.ai/api/v1",
        "key_env": "LLAMA_API_KEY",
        "model_env": "LLAMA_MODEL_ID",
        "url_env": "LLAMA_BASE_URL",
    },
    "GPT": {
        "provider": "openai_compatible",
        "model": "gpt-4o-mini",
        "label": "OpenAI GPT",
        "base_url_default": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL_ID",
        "url_env": "OPENAI_BASE_URL",
    },
    "EXAONE": {
        "provider": "openai_compatible",
        "model": "k-exaone_v2.5",
        "label": "LG EXAONE",
        "base_url_default": "https://api.exaone.ai/v1",
        "key_env": "EXAONE_API_KEY",
        "model_env": "EXAONE_MODEL_ID",
        "url_env": "EXAONE_BASE_URL",
    },
}


def _secret(name: str, default: str = "") -> str:
    """환경변수 → Streamlit secrets 순으로 조회. 키를 코드에 박지 않는다."""
    env_val = os.getenv(name, "").strip()
    if env_val:
        return env_val
    try:
        import streamlit as st

        if hasattr(st, "secrets") and name in st.secrets:
            value = st.secrets.get(name)
            if value is not None and str(value).strip():
                return str(value).strip()
    except Exception:
        pass
    return (default or "").strip()


@lru_cache
def runtime_settings() -> dict[str, Any]:
    models: dict[str, dict[str, Any]] = {}
    for name, spec in MODELS.items():
        models[name] = {
            "provider": spec["provider"],
            "label": spec["label"],
            "model": _secret(spec["model_env"], spec["model"]),
            "base_url": _secret(spec["url_env"], spec["base_url_default"]),
            "api_key": _secret(spec["key_env"]),
        }
    default = _secret("DEFAULT_MODEL", "Solar")
    if default not in models:
        default = next(iter(models))
    return {"models": models, "default_model": default}


def model_status(name: str) -> dict[str, Any]:
    cfg = runtime_settings()["models"][name]
    live = bool(cfg.get("api_key"))
    return {
        "name": name,
        "label": cfg.get("label", name),
        "provider": cfg["provider"],
        "model": cfg["model"],
        "live": live,
        "mode": "live" if live else "mock",
    }
