from __future__ import annotations

import multiprocessing
import os
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

import uvicorn
from PIL import Image, ImageDraw


def _server_url(host: str, port: int) -> str:
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    return f"http://{display_host}:{port}"


def _runtime_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _setup_runtime_log() -> None:
    if not getattr(sys, "frozen", False):
        return
    log_path = _runtime_dir() / "ATG_Document_Manager_Server.log"
    log_file = log_path.open("a", encoding="utf-8", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file
    print("\n--- ATG Document Manager server starting ---")


def _load_tray_image() -> Image.Image:
    from app.config import resource_path

    icon_path = resource_path("icon.ico")
    logo_path = resource_path("logo.png")
    for path in (icon_path, logo_path):
        try:
            return Image.open(path).resize((64, 64))
        except Exception:
            pass

    image = Image.new("RGBA", (64, 64), "#164875")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 56, 56), radius=10, fill="#0f6b8f")
    draw.text((18, 22), "ATG", fill="white")
    return image


def _run_with_tray(app, host: str, port: int) -> None:
    try:
        import pystray
    except ImportError:
        print("pystray is not installed; fallback to console server.")
        uvicorn.run(app, host=host, port=port, reload=False, access_log=True)
        return

    server_holder: dict[str, uvicorn.Server | None] = {"server": None}
    server_ready = threading.Event()

    def server_thread() -> None:
        server_config = uvicorn.Config(
            app,
            host=host,
            port=port,
            reload=False,
            access_log=False,
            log_level="info",
        )
        server = uvicorn.Server(server_config)
        server_holder["server"] = server
        server_ready.set()
        server.run()

    thread = threading.Thread(target=server_thread, name="ATGDocumentServer", daemon=True)
    thread.start()
    server_ready.wait(timeout=5)

    url = _server_url(host, port)

    def open_web(_icon=None, _item=None) -> None:
        webbrowser.open(url)

    def stop_server(icon, _item=None) -> None:
        server = server_holder.get("server")
        if server is not None:
            server.should_exit = True
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Mở web quản lý", open_web),
        pystray.MenuItem("Thoát server", stop_server),
    )
    tray_icon = pystray.Icon(
        "ATGDocumentManager",
        _load_tray_image(),
        "ATG Document Manager",
        menu,
    )
    tray_icon.run()

    server = server_holder.get("server")
    if server is not None:
        server.should_exit = True
    deadline = time.time() + 8
    while thread.is_alive() and time.time() < deadline:
        time.sleep(0.1)


def main() -> None:
    _setup_runtime_log()
    from app.config import get_config
    from app.main import app

    config = get_config()
    host = str(config.get("host", "0.0.0.0"))
    port = int(config.get("port", 8088))

    if "--console" in sys.argv or os.environ.get("ATG_SERVER_CONSOLE") == "1":
        print(f"ATG Document Manager server: {_server_url(host, port)}")
        print("Close this window or press Ctrl+C to stop the server.")
        uvicorn.run(app, host=host, port=port, reload=False, access_log=True)
        return

    _run_with_tray(app, host, port)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
