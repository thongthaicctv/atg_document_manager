from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "app_name": "ATG Document Manager",
    "host": "0.0.0.0",
    "port": 8088,
    "database": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "atg_doc_user",
        "password": "your_password",
        "database": "atg_document_system",
    },
    "storage": {
        "upload_dir": "D:/ATG_DOCUMENT/uploads",
        "max_file_size_mb": 50,
        "allowed_extensions": ["pdf", "jpg", "jpeg", "png", "doc", "docx", "xls", "xlsx"],
    },
    "security": {
        "session_timeout_minutes": 60,
        "password_min_length": 6,
        "secret_key": "change-this-secret-key-before-production",
    },
}


def _deep_merge(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = defaults.copy()
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@lru_cache
def get_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        user_config = json.load(fh)
    return _deep_merge(DEFAULT_CONFIG, user_config)


def get_database_url() -> str:
    db = get_config()["database"]
    user = quote_plus(str(db["user"]))
    password = quote_plus(str(db["password"]))
    database = quote_plus(str(db["database"]))
    return (
        f"mysql+pymysql://{user}:{password}"
        f"@{db['host']}:{db['port']}/{database}?charset=utf8mb4"
    )


def get_upload_dir() -> Path:
    upload_dir = Path(get_config()["storage"]["upload_dir"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir
