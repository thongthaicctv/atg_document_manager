from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import PROJECT_ROOT, get_config

APP_LICENSE_CODE = "ATG_DOCUMENT_MANAGER"
LICENSE_TOKEN_PREFIX = "ATG1-"
LICENSE_FILE_NAME = "license.key"

PUBLIC_KEY_N = int(
    "ce2171cd44068dcda094d2a550c41e06448deac0bba852c33306c64175901fed7d349405cea9cff4561fbb44da6c7a3291bc07eb7c6d675ac915626d798254fb57fffaf7abdad5278975196cba881e87cd7d1092583d055bb1bab0c96e1119bf5be86ab1351f2f980a65e802adf64f026b9f2c353a1f96ea597a1bc13255f6fd024943a18283d42093d44d109826b441cbc1d061be0a60925fcb6cedff594618deff193b6904bc1aa603a6c6138635a51cc25927f611bf7c924202d5948802fdf928ec45b0d02677da4c3ce2fab1d92c4e3331a73f779343eeeec34252586e2ed445e7bb6fd230d34fcee49a829ddc23c92e1077b0f2942797cf74556afb0db9",
    16,
)
PUBLIC_KEY_E = 65537

SHA256_DIGESTINFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")
GENERIC_MACHINE_VALUES = {
    "",
    "0",
    "none",
    "null",
    "unknown",
    "default string",
    "to be filled by o.e.m.",
    "system serial number",
    "not specified",
    "not applicable",
}


@dataclass(frozen=True)
class LicenseStatus:
    valid: bool
    message: str
    machine_code: str
    license_file: Path
    data: dict[str, Any] | None = None
    enforced: bool = True


def license_file_path() -> Path:
    config = get_config().get("license", {})
    configured_path = str(config.get("license_file", "")).strip()
    if configured_path:
        return Path(configured_path).expanduser()
    return PROJECT_ROOT / LICENSE_FILE_NAME


def license_enforced() -> bool:
    if os.environ.get("ATG_LICENSE_BYPASS") == "1":
        return False
    return bool(get_config().get("license", {}).get("enforce", True))


def normalize_machine_code(value: str) -> str:
    return re.sub(r"[^A-Fa-f0-9]", "", value or "").upper()


def _display_machine_code(value: str) -> str:
    clean = normalize_machine_code(value)
    return "-".join(clean[index : index + 4] for index in range(0, len(clean), 4))


def _clean_machine_value(value: str | None) -> str:
    clean = " ".join((value or "").strip().split())
    if clean.lower() in GENERIC_MACHINE_VALUES:
        return ""
    if set(clean) <= {"0", "-", " "}:
        return ""
    return clean


def _read_windows_machine_guid() -> str:
    if os.name != "nt":
        return ""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return _clean_machine_value(str(value))
    except OSError:
        return ""


def _read_wmic_value(alias: str, field: str) -> str:
    if os.name != "nt":
        return ""
    startupinfo = None
    creationflags = 0
    if hasattr(subprocess, "STARTUPINFO"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags = subprocess.CREATE_NO_WINDOW
    try:
        result = subprocess.run(
            ["wmic", alias, "get", field, "/value"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if result.returncode != 0:
        return ""
    prefix = f"{field}="
    for line in result.stdout.splitlines():
        if line.strip().lower().startswith(prefix.lower()):
            return _clean_machine_value(line.split("=", 1)[1])
    return ""


def _machine_fingerprint_parts() -> list[str]:
    candidates = [
        ("machine_guid", _read_windows_machine_guid()),
        ("computer_name", platform.node()),
        ("csproduct_uuid", _read_wmic_value("csproduct", "UUID")),
        ("bios_serial", _read_wmic_value("bios", "SerialNumber")),
        ("baseboard_serial", _read_wmic_value("baseboard", "SerialNumber")),
    ]
    parts: list[str] = []
    for key, value in candidates:
        clean = _clean_machine_value(value)
        if clean:
            parts.append(f"{key}={clean.lower()}")
    if not parts:
        parts.append(f"fallback={platform.platform().lower()}")
    return parts


@lru_cache(maxsize=1)
def get_machine_code() -> str:
    raw = "|".join(_machine_fingerprint_parts()).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest().upper()[:32]
    return _display_machine_code(digest)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    clean = value.strip()
    clean += "=" * (-len(clean) % 4)
    return base64.urlsafe_b64decode(clean.encode("ascii"))


def canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _expected_encoded_message(message: bytes, modulus_size: int) -> bytes:
    digest = hashlib.sha256(message).digest()
    digest_info = SHA256_DIGESTINFO_PREFIX + digest
    padding_len = modulus_size - len(digest_info) - 3
    if padding_len < 8:
        raise ValueError("RSA key is too short for SHA-256 signature.")
    return b"\x00\x01" + (b"\xff" * padding_len) + b"\x00" + digest_info


def rsa_sign_payload(payload: dict[str, Any], private_key: dict[str, Any]) -> bytes:
    message = canonical_payload_bytes(payload)
    n = int(str(private_key["n"]), 16)
    d = int(str(private_key["d"]), 16)
    modulus_size = (n.bit_length() + 7) // 8
    encoded = _expected_encoded_message(message, modulus_size)
    signature = pow(int.from_bytes(encoded, "big"), d, n)
    return signature.to_bytes(modulus_size, "big")


def build_license_token(payload: dict[str, Any], signature: bytes) -> str:
    payload_json = canonical_payload_bytes(payload)
    return LICENSE_TOKEN_PREFIX + _b64url_encode(payload_json) + "." + _b64url_encode(signature)


def parse_license_token(raw_license: str) -> tuple[dict[str, Any], bytes]:
    clean = re.sub(r"\s+", "", raw_license or "")
    if clean.startswith(LICENSE_TOKEN_PREFIX):
        clean = clean[len(LICENSE_TOKEN_PREFIX) :]
    parts = clean.split(".", 1)
    if len(parts) != 2:
        raise ValueError("License không đúng định dạng.")
    payload = json.loads(_b64url_decode(parts[0]).decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Nội dung license không hợp lệ.")
    return payload, _b64url_decode(parts[1])


def _verify_signature(payload: dict[str, Any], signature: bytes) -> bool:
    modulus_size = (PUBLIC_KEY_N.bit_length() + 7) // 8
    if len(signature) != modulus_size:
        return False
    message = canonical_payload_bytes(payload)
    expected = _expected_encoded_message(message, modulus_size)
    decoded_int = pow(int.from_bytes(signature, "big"), PUBLIC_KEY_E, PUBLIC_KEY_N)
    decoded = decoded_int.to_bytes(modulus_size, "big")
    return decoded == expected


def validate_license_key(raw_license: str) -> LicenseStatus:
    machine_code = get_machine_code()
    path = license_file_path()
    try:
        payload, signature = parse_license_token(raw_license)
    except Exception as exc:
        return LicenseStatus(False, str(exc), machine_code, path)

    if payload.get("app") != APP_LICENSE_CODE:
        return LicenseStatus(False, "License không dành cho ứng dụng này.", machine_code, path, payload)
    if normalize_machine_code(str(payload.get("machine_code", ""))) != normalize_machine_code(machine_code):
        return LicenseStatus(False, "License không khớp mã máy hiện tại.", machine_code, path, payload)
    if not _verify_signature(payload, signature):
        return LicenseStatus(False, "Chữ ký license không hợp lệ.", machine_code, path, payload)

    expires_at = str(payload.get("expires_at") or "").strip()
    if expires_at:
        try:
            expiry_date = date.fromisoformat(expires_at)
        except ValueError:
            return LicenseStatus(False, "Ngày hết hạn license không hợp lệ.", machine_code, path, payload)
        if expiry_date < date.today():
            return LicenseStatus(False, "License đã hết hạn.", machine_code, path, payload)

    return LicenseStatus(True, "License hợp lệ.", machine_code, path, payload)


def get_license_status() -> LicenseStatus:
    machine_code = get_machine_code()
    path = license_file_path()
    enforced = license_enforced()
    if not enforced:
        return LicenseStatus(True, "Đang tắt kiểm tra license cho môi trường phát triển.", machine_code, path, enforced=False)
    if not path.exists():
        return LicenseStatus(False, "Máy chủ chưa được gắn license.", machine_code, path, enforced=True)
    try:
        return validate_license_key(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return LicenseStatus(False, f"Không đọc được file license: {exc}", machine_code, path, enforced=True)


def install_license_key(raw_license: str) -> LicenseStatus:
    status = validate_license_key(raw_license)
    if not status.valid:
        raise ValueError(status.message)
    status.license_file.parent.mkdir(parents=True, exist_ok=True)
    status.license_file.write_text(re.sub(r"\s+", "", raw_license.strip()) + "\n", encoding="utf-8")
    return get_license_status()


def remove_license_key() -> None:
    path = license_file_path()
    if path.exists():
        path.unlink()
