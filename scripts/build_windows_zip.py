from __future__ import annotations

import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


PYTHON_VERSION = "3.12.10"
PYTHON_TAG = "312"
PYTHON_ABI = "cp312"
PACKAGE_NAME = "LLM-Evaluation-Demo"

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_ROOT = REPO_ROOT / "artifacts" / "windows"
DOWNLOAD_DIR = BUILD_ROOT / "downloads"
STAGE_ROOT = BUILD_ROOT / PACKAGE_NAME
ZIP_PATH = BUILD_ROOT / f"{PACKAGE_NAME}.zip"
PYTHON_ZIP_URL = (
    f"https://www.python.org/ftp/python/{PYTHON_VERSION}/"
    f"python-{PYTHON_VERSION}-embed-amd64.zip"
)


def main() -> None:
    step("Prepare clean staging directory", prepare_stage)
    step("Build frontend static assets", build_frontend)
    step("Copy application files", copy_application_files)
    step("Install embedded Windows Python runtime", install_embedded_python)
    step("Install Windows backend wheels", install_backend_wheels)
    step("Write Start.bat", write_start_script)
    step("Create ZIP package", create_zip)
    print(f"\nPackage created: {ZIP_PATH}")


def step(message: str, action) -> None:  # noqa: ANN001
    print(f"\n==> {message}", flush=True)
    action()


def run(command: list[str], cwd: Path | None = None) -> None:
    print(f"+ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def prepare_stage() -> None:
    if STAGE_ROOT.exists():
        shutil.rmtree(STAGE_ROOT)
    (STAGE_ROOT / "app" / "backend").mkdir(parents=True)
    (STAGE_ROOT / "data" / "uploads").mkdir(parents=True)
    (STAGE_ROOT / "logs").mkdir(parents=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def build_frontend() -> None:
    frontend_dir = REPO_ROOT / "frontend"
    if shutil.which("bun"):
        run(["bun", "install", "--no-save"], cwd=frontend_dir)
        run(["bun", "run", "build"], cwd=frontend_dir)
        return
    if shutil.which("npm"):
        run(["npm", "install"], cwd=frontend_dir)
        run(["npm", "run", "build"], cwd=frontend_dir)
        return
    raise RuntimeError("Neither bun nor npm was found. Install one build-time frontend runtime.")


def copy_application_files() -> None:
    copy_tree(REPO_ROOT / "backend" / "app", STAGE_ROOT / "app" / "backend" / "app")
    copy_tree(REPO_ROOT / "frontend" / "dist", STAGE_ROOT / "app" / "frontend_dist")
    copy_tree(REPO_ROOT / "images", STAGE_ROOT / "app" / "images")
    shutil.copy2(REPO_ROOT / "model.txt", STAGE_ROOT / "app" / "model.txt")
    shutil.copy2(REPO_ROOT / "requirements.txt", STAGE_ROOT / "app" / "backend" / "requirements.txt")


def copy_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def install_embedded_python() -> None:
    python_zip = DOWNLOAD_DIR / f"python-{PYTHON_VERSION}-embed-amd64.zip"
    runtime_root = STAGE_ROOT / "runtime" / "python"
    runtime_root.mkdir(parents=True, exist_ok=True)
    if not python_zip.exists():
        print(f"Downloading {PYTHON_ZIP_URL}", flush=True)
        urllib.request.urlretrieve(PYTHON_ZIP_URL, python_zip)

    with zipfile.ZipFile(python_zip) as archive:
        archive.extractall(runtime_root)

    pth_files = list(runtime_root.glob("python*._pth"))
    if not pth_files:
        raise RuntimeError("Embedded Python ._pth file was not found.")
    pth_file = pth_files[0]
    lines = pth_file.read_text(encoding="utf-8").splitlines()
    output: list[str] = []
    inserted_site_packages = False
    for line in lines:
        if not inserted_site_packages and line.endswith(".zip"):
            output.append(line)
            output.append(r"Lib\site-packages")
            inserted_site_packages = True
            continue
        output.append("import site" if line == "#import site" else line)
    if not inserted_site_packages:
        output.insert(0, r"Lib\site-packages")
    pth_file.write_text("\n".join(output) + "\n", encoding="ascii")


def install_backend_wheels() -> None:
    site_packages = STAGE_ROOT / "runtime" / "python" / "Lib" / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--target",
            str(site_packages),
            "--platform",
            "win_amd64",
            "--python-version",
            PYTHON_TAG,
            "--implementation",
            "cp",
            "--abi",
            PYTHON_ABI,
            "--only-binary=:all:",
            "--no-warn-script-location",
            "-r",
            str(REPO_ROOT / "requirements.txt"),
        ]
    )


def write_start_script() -> None:
    start_script = r"""@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

if not exist "%ROOT%logs" mkdir "%ROOT%logs"
if not exist "%ROOT%data\uploads" mkdir "%ROOT%data\uploads"

set "PYTHON_EXE=%ROOT%runtime\python\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Missing runtime Python: %PYTHON_EXE%
  pause
  exit /b 1
)

echo Starting LLM Evaluation Demo...
echo Logs: %ROOT%logs\server.log

powershell -NoProfile -ExecutionPolicy Bypass -Command "$env:LLM_EVAL_PACKAGE_ROOT=$env:ROOT; & (Join-Path $env:ROOT 'runtime\python\python.exe') (Join-Path $env:ROOT 'app\backend\app\package_server.py') 2>&1 | Tee-Object -FilePath (Join-Path $env:ROOT 'logs\server.log') -Append"

echo.
echo Application stopped.
pause
"""
    (STAGE_ROOT / "Start.bat").write_text(start_script, encoding="ascii", newline="\r\n")


def create_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(STAGE_ROOT.rglob("*")):
            archive.write(path, path.relative_to(STAGE_ROOT.parent))


if __name__ == "__main__":
    main()
