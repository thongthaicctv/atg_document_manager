from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes
import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
    BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    BUNDLE_ROOT = PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "config.json"
CONFIG_LOCK_PATH = PROJECT_ROOT / ".config_encrypted"

ENCRYPTED_CONFIG_MARKER = "__atg_encrypted_config__"
CONFIG_ENCRYPTION_VERSION = 1
CONFIG_DPAPI_ENTROPY = b"ATG Document Manager encrypted config v1"
CRYPTPROTECT_UI_FORBIDDEN = 0x1
CRYPTPROTECT_LOCAL_MACHINE = 0x4

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
    "network": {
        "allow_wan_access": True,
    },
    "backup": {
        "backup_dir": "D:/ATG_DOCUMENT/backup",
    },
    "license": {
        "enforce": True,
        "license_file": "",
    },
    "runtime": {
        "auto_start_windows": False,
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


def resource_path(*parts: str) -> Path:
    return BUNDLE_ROOT.joinpath(*parts)


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _blob_from_bytes(data: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(data)
    blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    return blob, buffer


def _require_windows_dpapi() -> None:
    if os.name != "nt":
        raise RuntimeError(
            "Config encryption requires Windows DPAPI. "
            "Set ATG_ALLOW_PLAINTEXT_CONFIG=1 only for development on non-Windows hosts."
        )


def _dpapi_protect(data: bytes) -> bytes:
    _require_windows_dpapi()
    in_blob, in_buffer = _blob_from_bytes(data)
    entropy_blob, entropy_buffer = _blob_from_bytes(CONFIG_DPAPI_ENTROPY)
    out_blob = _DataBlob()
    flags = CRYPTPROTECT_UI_FORBIDDEN | CRYPTPROTECT_LOCAL_MACHINE
    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        "ATG Document Manager config",
        ctypes.byref(entropy_blob),
        None,
        None,
        flags,
        ctypes.byref(out_blob),
    )
    # Keep input buffers alive until CryptProtectData returns.
    _ = (in_buffer, entropy_buffer)
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(ctypes.cast(out_blob.pbData, ctypes.c_void_p))


def _dpapi_unprotect(data: bytes) -> bytes:
    _require_windows_dpapi()
    in_blob, in_buffer = _blob_from_bytes(data)
    entropy_blob, entropy_buffer = _blob_from_bytes(CONFIG_DPAPI_ENTROPY)
    out_blob = _DataBlob()
    flags = CRYPTPROTECT_UI_FORBIDDEN
    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        flags,
        ctypes.byref(out_blob),
    )
    _ = (in_buffer, entropy_buffer)
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(ctypes.cast(out_blob.pbData, ctypes.c_void_p))


def _plaintext_config_allowed() -> bool:
    return os.environ.get("ATG_ALLOW_PLAINTEXT_CONFIG") == "1"


def _is_encrypted_config(file_data: Any) -> bool:
    return isinstance(file_data, dict) and file_data.get(ENCRYPTED_CONFIG_MARKER) is True


def _decrypt_config_payload(file_data: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = base64.b64decode(str(file_data["payload"]))
        plaintext = _dpapi_unprotect(payload)
        decrypted = json.loads(plaintext.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("Không giải mã được config.json. Kiểm tra đúng máy cài server hoặc tạo lại cấu hình.") from exc
    if not isinstance(decrypted, dict):
        raise RuntimeError("Nội dung config.json sau giải mã không hợp lệ.")
    return decrypted


def _write_encrypted_config(config: dict[str, Any]) -> None:
    if _plaintext_config_allowed():
        with CONFIG_PATH.open("w", encoding="utf-8") as fh:
            json.dump(config, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        return

    plaintext = json.dumps(config, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    payload = base64.b64encode(_dpapi_protect(plaintext)).decode("ascii")
    encrypted_file = {
        ENCRYPTED_CONFIG_MARKER: True,
        "version": CONFIG_ENCRYPTION_VERSION,
        "provider": "windows-dpapi-local-machine",
        "payload": payload,
    }
    with CONFIG_PATH.open("w", encoding="utf-8") as fh:
        json.dump(encrypted_file, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    CONFIG_LOCK_PATH.write_text("encrypted\n", encoding="utf-8")


@lru_cache
def get_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG
    with CONFIG_PATH.open("r", encoding="utf-8-sig") as fh:
        file_data = json.load(fh)

    if _is_encrypted_config(file_data):
        user_config = _decrypt_config_payload(file_data)
    else:
        if CONFIG_LOCK_PATH.exists() and not _plaintext_config_allowed():
            raise RuntimeError("config.json phải được mã hóa. Không chấp nhận cấu hình dạng plaintext sau khi đã khóa mã hóa.")
        if not isinstance(file_data, dict):
            raise RuntimeError("config.json không hợp lệ.")
        user_config = file_data

    merged = _deep_merge(DEFAULT_CONFIG, user_config)
    if not _is_encrypted_config(file_data) and not _plaintext_config_allowed():
        _write_encrypted_config(merged)
    return merged


def save_config(config: dict[str, Any]) -> None:
    merged = _deep_merge(DEFAULT_CONFIG, config)
    _write_encrypted_config(merged)
    get_config.cache_clear()


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
