from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

import uvicorn


def main() -> None:
    package_root, package_app_dir = resolve_package_paths()
    data_dir = package_root / "data"
    backend_dir = package_app_dir / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    os.environ.setdefault("LLM_EVAL_PROJECT_ROOT", str(package_app_dir))
    os.environ.setdefault("LLM_EVAL_MODEL_FILE", str(package_app_dir / "model.txt"))
    os.environ.setdefault("LLM_EVAL_SAMPLE_ASSETS_DIR", str(package_app_dir / "images"))
    os.environ.setdefault("LLM_EVAL_FRONTEND_DIST_DIR", str(package_app_dir / "frontend_dist"))
    os.environ.setdefault("LLM_EVAL_UPLOADS_DIR", str(data_dir / "uploads"))

    (data_dir / "uploads").mkdir(parents=True, exist_ok=True)
    (package_root / "logs").mkdir(parents=True, exist_ok=True)

    host = "127.0.0.1"
    port = int(os.environ.get("LLM_EVAL_PORT") or find_free_port(host))
    url = f"http://{host}:{port}"

    print(f"LLM Evaluation Demo starting at {url}", flush=True)
    print(f"Package root: {package_root}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)

    threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    uvicorn.run("app.main:app", host=host, port=port, reload=False, access_log=True)


def resolve_package_paths() -> tuple[Path, Path]:
    env_root = os.environ.get("LLM_EVAL_PACKAGE_ROOT")
    if env_root:
        package_root = Path(env_root).expanduser().resolve()
        return package_root, package_root / "app"

    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "app" / "backend").exists() and (parent / "Start.bat").exists():
            return parent, parent / "app"

    source_root = current.parents[2]
    return source_root, source_root


def find_free_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def open_when_ready(url: str) -> None:
    health_url = f"{url}/health"
    for _ in range(60):
        try:
            with urllib.request.urlopen(health_url, timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except OSError:
            time.sleep(0.5)
    print(f"Server did not become ready automatically. Open manually: {url}", flush=True)


if __name__ == "__main__":
    main()
