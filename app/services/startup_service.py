from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from app.config import PROJECT_ROOT

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "ATGDocumentManagerServer"


@dataclass(frozen=True)
class StartupStatus:
    available: bool
    enabled: bool
    command: str
    expected_command: str
    message: str


def _quote(value: str | Path) -> str:
    return f'"{value}"'


def _command_executable_path(command: str) -> Path | None:
    command = command.strip()
    if not command:
        return None
    if command.startswith('"'):
        end_quote = command.find('"', 1)
        if end_quote > 1:
            return Path(command[1:end_quote])
    return Path(command.split(maxsplit=1)[0])


def _find_packaged_server() -> Path | None:
    exact_path = PROJECT_ROOT / "dist" / "ATG_Document_Manager_Server.exe"
    if exact_path.exists():
        return exact_path

    dist_dir = PROJECT_ROOT / "dist"
    if not dist_dir.exists():
        return None
    candidates = sorted(
        dist_dir.glob("ATG_Document_Manager_Server*.exe"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def build_startup_command() -> str:
    if getattr(sys, "frozen", False):
        return _quote(Path(sys.executable).resolve())

    packaged_server = _find_packaged_server()
    if packaged_server:
        return _quote(packaged_server)

    pythonw = Path(sys.executable).with_name("pythonw.exe")
    python_exe = pythonw if pythonw.exists() else Path(sys.executable)
    server_script = PROJECT_ROOT / "server_onefile.py"
    return f"{_quote(python_exe)} {_quote(server_script)}"


def _require_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("Tự khởi động cùng Windows chỉ hỗ trợ trên Windows.")


def get_startup_status() -> StartupStatus:
    expected_command = build_startup_command()
    if os.name != "nt":
        return StartupStatus(
            available=False,
            enabled=False,
            command="",
            expected_command=expected_command,
            message="Máy hiện tại không phải Windows.",
        )

    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
            command, _value_type = winreg.QueryValueEx(key, RUN_VALUE_NAME)
    except FileNotFoundError:
        return StartupStatus(
            available=True,
            enabled=False,
            command="",
            expected_command=expected_command,
            message="Chưa bật tự khởi động cùng Windows.",
        )
    command_text = str(command)
    executable_path = _command_executable_path(command_text)
    command_exists = bool(executable_path and executable_path.exists())
    command_matches = command_text.strip().lower() == expected_command.strip().lower()
    if not command_exists:
        message = "Đã bật tự khởi động nhưng đường dẫn server không còn tồn tại. Bấm Lưu cài đặt để cập nhật lại."
    elif not command_matches:
        message = "Đã bật tự khởi động nhưng đang trỏ tới lệnh cũ. Bấm Lưu cài đặt để cập nhật lại."
    else:
        message = "Đã bật tự khởi động cùng Windows."
    return StartupStatus(
        available=True,
        enabled=command_exists and command_matches,
        command=command_text,
        expected_command=expected_command,
        message=message,
    )


def set_auto_start(enabled: bool) -> StartupStatus:
    _require_windows()

    import winreg

    command = build_startup_command()
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, RUN_VALUE_NAME, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, RUN_VALUE_NAME)
            except FileNotFoundError:
                pass
    return get_startup_status()
