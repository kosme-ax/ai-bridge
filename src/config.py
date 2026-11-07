from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# 모델 이름은 UI에만 쓰고, 실제 호출은 provider/model 설정으로만 한다.
MODELS: dict[str, dict[str, str]] = {
    "Solar": {
        "provider": "upstage",
        "model": "solar-pro4",
        "label": "Upstage Solar",
    },
    "Gemini": {
        "provider": "google",
        "model": "gemini-2.0-flash",
        "label": "Google Gemini",
    },
}


def _secret(name: str, default: str = "") -> str:
    """Streamlit secrets → 환경변수 순으로 조회. 키를 코드에 박지 않는다."""
    try:
        import streamlit as st

        if hasattr(st, "secrets") and name in st.secrets:
            value = st.secrets.get(name)
            if value is not None and str(value).strip():
                return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()


@lru_cache
def runtime_settings() -> dict[str, Any]:
    models = {
        "Solar": {
            **MODELS["Solar"],
            "model": _secret("SOLAR_MODEL_ID", MODELS["Solar"]["model"]),
            "base_url": _secret("SOLAR_BASE_URL", "https://api.upstage.ai/v1"),
            "api_key": _secret("SOLAR_API_KEY"),
        },
        "Gemini": {
            **MODELS["Gemini"],
            "model": _secret("GEMINI_MODEL_ID", MODELS["Gemini"]["model"]),
            "base_url": _secret("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
            "api_key": _secret("GEMINI_API_KEY"),
        },
    }
    default = _secret("DEFAULT_MODEL", "Solar")
    if default not in models:
        default = "Solar"
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
