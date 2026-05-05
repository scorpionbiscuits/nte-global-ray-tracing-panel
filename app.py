from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
import winreg
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


APP_VERSION = "0.1.6"
APP_CN_NAME = "NTE Ray Tracing Unlock Panel"
APP_FULL_CN_NAME = "Neverness To Everness Ray Tracing / Path Tracing One-Click Unlock Tool"
APP_EN_NAME = "NTE Ray Tracing Panel"
APP_SEARCH_KEYWORDS = [
    "NTE ray tracing unlock",
    "NTE ray tracing fix",
    "NTE ray tracing tool",
    "NTE one-click ray tracing unlock",
    "NTE one-click OptiScaler install",
    "NTE no ray tracing option",
    "NTE ray tracing option missing",
    "NTE ray tracing not showing",
    "NTE GPU spoof",
    "NTE OptiScaler DXGI spoof",
    "Neverness To Everness ray tracing unlock",
    "Neverness To Everness ray tracing fix",
    "Neverness To Everness no ray tracing option",
    "Ananta ray tracing unlock",
    "Ananta path tracing",
]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 22642
GITHUB_RELEASE_API = "https://api.github.com/repos/optiscaler/OptiScaler/releases/latest"
GAME_EXE = "HTGame.exe"
GAME_EXE_CANDIDATES = ("HTGame.exe", "NTEGame.exe", "NTEGlobalGame.exe")
SEVEN_ZIPR_URL = "https://github.com/ip7z/7zip/releases/download/26.01/7zr.exe"
DEFAULT_GAME_PATH = r"C:\Program Files\Neverness To Everness\Client\WindowsNoEditor\HT\Binaries\Win64\HTGame.exe"

RUN_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", RUN_DIR))
WEB_DIR = RESOURCE_DIR / "web"
TOOLS_DIR = RUN_DIR / "tools" / "optiscaler"

MANAGED_FILES = (
    "winmm.dll",
    "OptiScaler.ini",
    "OptiScaler.log",
    "dlsstweaks.ini",
    "dlsstweaks.log",
)
MANAGED_DIRS = ("OptiScaler",)
BACKUP_DIR_NAME = "_nte_rt_backups"

FALLBACK_LOCAL_PROFILE = {
    "id": "local",
    "label": "Current GPU (Local)",
    "gpuName": "NVIDIA GeForce RTX 5060 Laptop GPU",
    "vendorId": "0x10de",
    "deviceId": "0x2d19",
    "vramGb": "auto",
    "description": "Uses the detected local NVIDIA GPU name and DeviceId. Use this to restore normal GPU identity.",
}

STATIC_PROFILES = {
    "rtx4090": {
        "id": "rtx4090",
        "label": "RTX 4090",
        "gpuName": "NVIDIA GeForce RTX 4090",
        "vendorId": "0x10de",
        "deviceId": "0x2684",
        "vramGb": "16",
        "description": "Previously verified whitelist target, desktop RTX 4090 identity.",
    },
    "rtx5080m": {
        "id": "rtx5080m",
        "label": "RTX 5080M",
        "gpuName": "NVIDIA GeForce RTX 5080 Laptop GPU",
        "vendorId": "0x10de",
        "deviceId": "0x2C59",
        "vramGb": "16",
        "description": "Mobile RTX 5080 Laptop GPU identity, suitable for testing 50-series whitelist.",
    },
}
DEFAULT_PROFILE_ID = "rtx5080m"


class DownloadProgress:
    """Thread-safe download progress state shared between the download thread and SSE stream."""
    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        with self._lock:
            self.active = False
            self.phase = "idle"       # idle | downloading | extracting | done | error
            self.filename = ""
            self.downloaded = 0
            self.total = 0
            self.error = ""

    def update(self, downloaded: int, total: int):
        with self._lock:
            self.downloaded = downloaded
            self.total = total

    def set_phase(self, phase: str, filename: str = ""):
        with self._lock:
            self.phase = phase
            self.active = phase not in ("idle", "done", "error")
            if filename:
                self.filename = filename

    def set_error(self, msg: str):
        with self._lock:
            self.phase = "error"
            self.active = False
            self.error = msg

    def snapshot(self) -> dict:
        with self._lock:
            pct = round(self.downloaded / self.total * 100, 1) if self.total > 0 else 0
            return {
                "phase": self.phase,
                "filename": self.filename,
                "downloaded": self.downloaded,
                "total": self.total,
                "pct": pct,
                "error": self.error,
            }

DOWNLOAD_PROGRESS = DownloadProgress()


class AppError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def safe_log(message: str, *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    if stream is None:
        return
    try:
        stream.write(message + "\n")
        stream.flush()
    except Exception:
        pass


def open_browser_safe(url: str) -> None:
    """
    Open a URL without elevation. webbrowser.open() raises WinError 5 when the
    calling process is elevated (admin) because Windows blocks spawning
    low-integrity processes (browsers) from high-integrity parents.
    Launching via explorer.exe de-escalates the open — it is the standard fix.
    """
    try:
        subprocess.Popen(["explorer.exe", url])
        return
    except Exception:
        pass
    try:
        webbrowser.open(url)
        return
    except Exception:
        pass
    safe_log(f"Auto-open browser failed (running as admin?). Open manually: {url}")


def raise_if_access_denied(exc: OSError, path: str = "") -> None:
    """Re-raise OSError with an actionable message when it is WinError 5."""
    if getattr(exc, "winerror", None) == 5:
        loc = f"\nPath: {path}" if path else ""
        raise AppError(
            f"Write access denied (WinError 5 Access Denied).{loc}\n\n"
            "Common causes and fixes:\n"
            "① Windows Defender real-time protection is blocking the winmm.dll write — "
            "add the game's Win64 folder to Exclusions in Windows Security → Virus & threat protection → Exclusions, then retry.\n"
            "② The game is installed under C:\\Program Files and the UAC token is not fully elevated — "
            "run this tool as Administrator, or move the game outside of Program Files (e.g. D:\\Games).",
            500,
        ) from exc
    raise exc


def now_id() -> str:
    stamp = datetime.now()
    return stamp.strftime("%Y%m%d-%H%M%S") + f"-{stamp.microsecond // 1000:03d}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def ensure_under(path: Path, base: Path) -> Path:
    resolved = path.resolve()
    root = base.resolve()
    if resolved != root and root not in resolved.parents:
        raise AppError(f"Refused to operate on path outside working directory: {resolved}", 500)
    return resolved


def run_command(args: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def run_powershell(script: str, *, timeout: int = 15) -> str:
    proc = run_command(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise AppError(proc.stderr.strip() or "PowerShell command failed.", 500)
    return proc.stdout.strip()


def running_processes() -> list[dict]:
    try:
        text = run_powershell(
            "Get-Process HTGame,NTEGame,NTEBrowser,NTEWebBooster,NTEGlobalGame,NTEGlobalLauncher,NTEGlobalBrowser,NTEGlobalWebBooster -ErrorAction SilentlyContinue | "
            "Select-Object ProcessName,Id,Path | ConvertTo-Json -Compress",
            timeout=8,
        )
    except Exception:
        return []
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    return data if isinstance(data, list) else []


def close_game_processes() -> list[dict]:
    before = running_processes()
    if not before:
        return []
    run_powershell(
        "Get-Process HTGame,NTEGame,NTEBrowser,NTEWebBooster,NTEGlobalGame,NTEGlobalLauncher,NTEGlobalBrowser,NTEGlobalWebBooster -ErrorAction SilentlyContinue | Stop-Process -Force",
        timeout=15,
    )
    time.sleep(1.5)
    return before


def procmon_filter_state() -> dict:
    try:
        proc = run_command(["fltmc", "filters"], timeout=6)
    except Exception as exc:
        return {"available": False, "present": False, "message": str(exc)}
    text = (proc.stdout or "") + (proc.stderr or "")
    present = "PROCMON" in text.upper()
    return {
        "available": proc.returncode == 0,
        "present": present,
        "message": "Process Monitor kernel filter driver detected. Reboot before launching the game." if present else "No Process Monitor filter driver detected.",
    }


def get_nvidia_adapters() -> list[dict]:
    try:
        text = run_powershell(
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,PNPDeviceID,DriverVersion,AdapterRAM,VideoProcessor | ConvertTo-Json -Compress",
            timeout=10,
        )
    except Exception:
        return []
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    rows = []
    for item in data:
        pnp = item.get("PNPDeviceID") or ""
        if "VEN_10DE" not in pnp.upper() and "NVIDIA" not in (item.get("Name") or "").upper():
            continue
        device_match = re.search(r"DEV_([0-9A-Fa-f]{4})", pnp)
        device_id = f"0x{device_match.group(1).lower()}" if device_match else None
        item["DeviceIdHex"] = device_id
        item["Registry"] = read_device_registry(pnp)
        rows.append(item)
    return rows


def local_profile_from_adapter(adapters: list[dict] | None = None) -> dict:
    profile = dict(FALLBACK_LOCAL_PROFILE)
    adapter = adapters[0] if adapters else None
    if adapter:
        profile["gpuName"] = adapter.get("Name") or profile["gpuName"]
        profile["deviceId"] = adapter.get("DeviceIdHex") or profile["deviceId"]
        profile["description"] = f"Detected local GPU: {profile['gpuName']} / {profile['deviceId']}."
    return profile


def spoof_profiles(adapters: list[dict] | None = None) -> list[dict]:
    return [
        local_profile_from_adapter(adapters),
        dict(STATIC_PROFILES["rtx4090"]),
        dict(STATIC_PROFILES["rtx5080m"]),
    ]


def resolve_profile(profile_id: str | None, adapters: list[dict] | None = None) -> dict:
    selected = (profile_id or DEFAULT_PROFILE_ID).strip().lower()
    if selected == "local":
        return local_profile_from_adapter(adapters)
    if selected in STATIC_PROFILES:
        return dict(STATIC_PROFILES[selected])
    raise AppError("Invalid GPU spoof profile.")


def read_device_registry(pnp_device_id: str) -> dict:
    if not pnp_device_id:
        return {}
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"SYSTEM\CurrentControlSet\Enum\{pnp_device_id}") as key:
            result = {}
            for value in ("DeviceDesc", "FriendlyName"):
                try:
                    result[value], _ = winreg.QueryValueEx(key, value)
                except FileNotFoundError:
                    result[value] = None
            return result
    except OSError:
        return {}


def expand_user_path(value: str | None) -> Path:
    if not value or not value.strip():
        raise AppError("Please select or enter the game path.")
    cleaned = value.strip().strip('"')
    return Path(os.path.expandvars(cleaned)).expanduser()


def likely_game_paths(base: Path) -> list[Path]:
    subdirs = [
        Path("."),
        Path("Client") / "WindowsNoEditor" / "HT" / "Binaries" / "Win64",
        Path("WindowsNoEditor") / "HT" / "Binaries" / "Win64",
        Path("HT") / "Binaries" / "Win64",
        Path("Binaries") / "Win64",
    ]
    return [
        base / subdir / exe
        for subdir in subdirs
        for exe in GAME_EXE_CANDIDATES
    ]


def limited_find_game(base: Path, limit: int = 160000) -> Path | None:
    if not base.is_dir():
        return None
    skipped = {"$RECYCLE.BIN", "System Volume Information", "Saved", "Logs", "UserData", "cef_cache_0"}
    checked = 0
    exe_set = {e.lower() for e in GAME_EXE_CANDIDATES}
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in skipped and not d.startswith(".")]
        checked += len(files)
        for f in files:
            if f.lower() in exe_set:
                return Path(root) / f
        if checked > limit:
            break
    return None


def detect_game(path_value: str | None) -> dict:
    base = expand_user_path(path_value)
    if not base.exists():
        raise AppError("Path does not exist.")
    exe: Path | None = None
    if base.is_file():
        if base.name.lower() not in {e.lower() for e in GAME_EXE_CANDIDATES}:
            raise AppError("Please select the NTE install root, the Win64 folder, or the game executable (HTGame.exe / NTEGlobalGame.exe).")
        exe = base
    else:
        for candidate in likely_game_paths(base):
            if candidate.is_file():
                exe = candidate
                break
        if exe is None:
            exe = limited_find_game(base)
    if exe is None:
        raise AppError("Game executable not found (HTGame.exe or NTEGlobalGame.exe).")
    win64 = exe.parent
    return {
        "input": str(base),
        "exe": str(exe),
        "exeName": exe.name,
        "win64": str(win64),
        "install": inspect_install(win64),
        "backups": list_backups(win64),
    }


def common_game_candidates() -> list[Path]:
    candidates = []
    # Env override takes highest priority
    if os.environ.get("NTE_GAME_PATH"):
        candidates.append(Path(os.environ["NTE_GAME_PATH"]))
    # Known default install path for the global PC release — checked first so
    # most users get instant auto-detection without any drive scan
    candidates.append(Path(DEFAULT_GAME_PATH))
    # Fallback: scan all drives for alternative install locations
    for drive in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        for base in (
            f"{drive}:\\Neverness To Everness",
            f"{drive}:\\Program Files\\Neverness To Everness",
            f"{drive}:\\Program Files (x86)\\Neverness To Everness",
        ):
            p = Path(base)
            candidates.append(p)
            candidates.append(p / "NTEGlobal")
    return candidates


def detect_common_game() -> dict | None:
    for candidate in common_game_candidates():
        try:
            if candidate.exists():
                return detect_game(str(candidate))
        except Exception:
            continue
    return None


def run_folder_dialog() -> str | None:
    script = r"""
Add-Type -AssemblyName System.Windows.Forms
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = 'Select the NTE install root folder, or the Win64 folder containing HTGame.exe'
$dialog.ShowNewFolderButton = $false
$form = New-Object System.Windows.Forms.Form
$form.TopMost = $true
$form.ShowInTaskbar = $false
$form.Width = 1
$form.Height = 1
$form.StartPosition = 'CenterScreen'
$result = $dialog.ShowDialog($form)
if ($result -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $dialog.SelectedPath }
"""
    proc = run_command(
        ["powershell", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-Command", script],
        timeout=120,
    )
    if proc.returncode != 0:
        raise AppError(proc.stderr.strip() or "Folder picker failed to launch.", 500)
    selected = proc.stdout.strip()
    return selected or None


def fetch_latest_release() -> dict:
    request = urllib.request.Request(GITHUB_RELEASE_API, headers={"User-Agent": "nte-ray-tracing-panel"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    assets = data.get("assets") or []
    asset = next((item for item in assets if str(item.get("name", "")).lower().endswith(".7z")), None)
    if not asset:
        raise AppError("No .7z asset found in the latest OptiScaler release.", 502)
    return {
        "tag": data.get("tag_name"),
        "name": data.get("name"),
        "url": data.get("html_url"),
        "published": data.get("published_at"),
        "assetName": asset.get("name"),
        "assetUrl": asset.get("browser_download_url"),
    }


def download_file(url: str, target: Path, *, on_progress: callable = None) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "nte-ray-tracing-panel"})
    with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as fh:
        total = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        chunk_size = 64 * 1024
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            fh.write(chunk)
            downloaded += len(chunk)
            if on_progress:
                on_progress(downloaded, total)


def find_optiscaler_stage() -> dict | None:
    if not TOOLS_DIR.is_dir():
        return None
    candidates = []
    for folder in TOOLS_DIR.iterdir():
        if not folder.is_dir():
            continue
        dll = next(folder.rglob("OptiScaler.dll"), None)
        ini = next(folder.rglob("OptiScaler.ini"), None)
        if dll and ini:
            candidates.append((folder.stat().st_mtime, folder, dll, ini))
    if not candidates:
        return None
    _, folder, dll, ini = sorted(candidates, reverse=True)[0]
    return {"dir": str(folder), "dll": str(dll), "ini": str(ini), "tag": folder.name}


def seven_zip_candidates() -> list[Path]:
    candidates: list[Path] = []
    for exe in ("7z", "7za", "7zr"):
        found = shutil.which(exe)
        if found:
            candidates.append(Path(found))
    for path in (
        RESOURCE_DIR / "tools" / "7zr.exe",
        RUN_DIR / "tools" / "7zr.exe",
        TOOLS_DIR / "_bin" / "7zr.exe",
    ):
        if path.is_file():
            candidates.append(path)
    return candidates


def ensure_seven_zipr() -> Path:
    for candidate in seven_zip_candidates():
        return candidate
    target = TOOLS_DIR / "_bin" / "7zr.exe"
    DOWNLOAD_PROGRESS.set_phase("downloading", "7zr.exe")
    download_file(SEVEN_ZIPR_URL, target, on_progress=DOWNLOAD_PROGRESS.update)
    if not target.is_file() or target.stat().st_size < 100_000:
        raise AppError("7zr.exe download failed or produced an invalid file.", 500)
    return target


def extract_with_seven_zip(seven_zip: Path, archive: Path, extract_dir: Path) -> tuple[bool, str]:
    proc = run_command([str(seven_zip), "x", "-y", f"-o{extract_dir}", str(archive)], timeout=180)
    if proc.returncode == 0:
        return True, ""
    return False, (proc.stderr or proc.stdout or f"{seven_zip.name} failed").strip()


def extract_optiscaler_archive(archive: Path, extract_dir: Path) -> None:
    errors = []

    try:
        seven_zip = ensure_seven_zipr()
        ok, error = extract_with_seven_zip(seven_zip, archive, extract_dir)
        if ok:
            return
        errors.append(error)
    except Exception as exc:
        errors.append(f"7zr: {exc}")

    try:
        import py7zr  # type: ignore
        with py7zr.SevenZipFile(archive, mode="r") as zf:
            zf.extractall(path=extract_dir)
        return
    except ImportError:
        errors.append("py7zr is not installed")
    except Exception as exc:
        errors.append(f"py7zr: {exc}")

    tar = shutil.which("tar")
    if tar:
        proc = run_command([tar, "-xf", str(archive), "-C", str(extract_dir)], timeout=180)
        if proc.returncode == 0:
            return
        errors.append((proc.stderr or proc.stdout or "tar failed").strip())
    else:
        errors.append("Windows tar.exe was not found")

    detail = "; ".join(item for item in errors if item)
    raise AppError(
        "OptiScaler archive extraction failed. Could not extract the .7z archive. " + detail,
        500,
    )


def ensure_optiscaler(force: bool = False) -> dict:
    existing = find_optiscaler_stage()
    if existing and not force:
        existing["downloaded"] = False
        return existing
    DOWNLOAD_PROGRESS.reset()
    DOWNLOAD_PROGRESS.set_phase("idle")
    try:
        release = fetch_latest_release()
        archive = TOOLS_DIR / str(release["assetName"])
        extract_dir = TOOLS_DIR / str(release["tag"])
        if force and extract_dir.exists():
            ensure_under(extract_dir, TOOLS_DIR)
            shutil.rmtree(extract_dir)
        if force or not archive.is_file():
            DOWNLOAD_PROGRESS.set_phase("downloading", release["assetName"])
            download_file(str(release["assetUrl"]), archive, on_progress=DOWNLOAD_PROGRESS.update)
        DOWNLOAD_PROGRESS.set_phase("extracting", release["assetName"])
        extract_dir.mkdir(parents=True, exist_ok=True)
        extract_optiscaler_archive(archive, extract_dir)
        stage = find_optiscaler_stage()
        if not stage:
            raise AppError("OptiScaler was downloaded but OptiScaler.dll was not found.", 500)
        stage.update({"downloaded": True, "release": release, "archive": str(archive)})
        DOWNLOAD_PROGRESS.set_phase("done")
        return stage
    except AppError:
        DOWNLOAD_PROGRESS.set_error("Download or extraction failed.")
        raise
    except Exception as exc:
        DOWNLOAD_PROGRESS.set_error(str(exc))
        raise


def list_backups(win64: Path) -> list[dict]:
    root = win64 / BACKUP_DIR_NAME
    if not root.is_dir():
        return []
    rows = []
    for folder in sorted(root.iterdir(), reverse=True):
        manifest = folder / "manifest.json"
        if not manifest.is_file():
            continue
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        rows.append({
            "id": folder.name,
            "path": str(folder),
            "created": data.get("created"),
            "mode": data.get("mode"),
            "profile": data.get("profile", {}).get("label") or data.get("profile", {}).get("gpuName"),
            "operations": data.get("operations", []),
        })
    return rows


def read_ini_values(path: Path) -> dict:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    wanted = {
        "SpoofedGPUName",
        "SpoofedVendorId",
        "SpoofedDeviceId",
        "TargetVendorId",
        "TargetDeviceId",
        "StreamlineSpoofing",
        "Dxgi",
        "DxgiVRAM",
        "Registry",
        "User32",
        "UseFakenvapi",
        "TargetProcessName",
        "OptiDllPath",
    }
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$", line)
        if match and match.group(1) in wanted:
            values[match.group(1)] = match.group(2)
    return values


def read_log_summary(path: Path) -> dict:
    if not path.is_file():
        return {"exists": False, "loaded": False, "spoofMentioned": False, "tail": ""}
    text = path.read_text(encoding="utf-8", errors="replace")
    tail = "\n".join(text.splitlines()[-120:])
    return {
        "exists": True,
        "size": path.stat().st_size,
        "modified": path.stat().st_mtime,
        "loaded": "OptiScaler" in text or "DLSSTweaks" in text,
        "spoofMentioned": "Spoof" in text or "spoof" in text,
        "tail": tail,
    }


def inspect_install(win64: Path) -> dict:
    winmm = win64 / "winmm.dll"
    opt_ini = win64 / "OptiScaler.ini"
    opt_dir = win64 / "OptiScaler"
    info = {
        "win64": str(win64),
        "installed": winmm.is_file() and opt_ini.is_file(),
        "winmm": None,
        "optScalerIni": read_ini_values(opt_ini),
        "optScalerDirExists": opt_dir.is_dir(),
        "log": read_log_summary(win64 / "OptiScaler.log"),
        "legacyDlsstweaksIni": (win64 / "dlsstweaks.ini").is_file(),
    }
    if winmm.is_file():
        info["winmm"] = {
            "size": winmm.stat().st_size,
            "modified": winmm.stat().st_mtime,
            "sha256": sha256(winmm),
            "looksLikeOptiScaler": winmm.stat().st_size > 5_000_000,
        }
    return info


def backup_path_for(rel: str, backup_dir: Path) -> Path:
    return backup_dir / "files" / rel


def backup_item(game_dir: Path, rel: str, backup_dir: Path, *, kind: str) -> dict:
    source = ensure_under(game_dir / rel, game_dir)
    record = {"rel": rel, "kind": kind, "existed": source.exists()}
    if not source.exists():
        return record
    destination = backup_path_for(rel, backup_dir)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination)
        record["backupRel"] = str(Path("files") / rel)
    else:
        shutil.copy2(source, destination)
        record.update({
            "backupRel": str(Path("files") / rel),
            "size": source.stat().st_size,
            "sha256": sha256(source),
        })
    return record


def restore_item(game_dir: Path, backup_dir: Path, record: dict) -> str:
    rel = record["rel"]
    target = ensure_under(game_dir / rel, game_dir)
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    if record.get("existed") and record.get("backupRel"):
        source = ensure_under(backup_dir / record["backupRel"], backup_dir)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return f"Restored {rel}"
    return f"Removed {rel}"


def set_ini_value(lines: list[str], key: str, value: str) -> list[str]:
    pattern = re.compile(r"^\s*" + re.escape(key) + r"\s*=")
    changed = False
    out = []
    for line in lines:
        if not changed and pattern.match(line):
            out.append(f"{key}={value}")
            changed = True
        else:
            out.append(line)
    if not changed:
        out.append(f"{key}={value}")
    return out


def build_optiscaler_config(template: Path, *, mode: str, target_device_id: str | None, profile: dict, exe_name: str = GAME_EXE) -> str:
    lines = template.read_text(encoding="utf-8", errors="replace").splitlines()
    values = {
        "SpoofedVendorId": profile["vendorId"],
        "SpoofedDeviceId": profile["deviceId"],
        "TargetVendorId": "0x10de",
        "TargetDeviceId": target_device_id or "auto",
        "SpoofedGPUName": profile["gpuName"],
        "OptiDllPath": r".\OptiScaler",
        "StreamlineSpoofing": "true",
        "Dxgi": "true",
        "DxgiFactoryWrapping": "false",
        "DxgiVRAM": profile["vramGb"],
        "Registry": "true" if mode == "full" else "false",
        "User32": "true" if mode == "full" else "false",
        "UseFakenvapi": "true" if mode == "full" else "false",
        "TargetProcessName": exe_name,
        "LogToFile": "true",
        "LogLevel": "0",
        "SingleFile": "true",
        "CheckForUpdate": "false",
    }
    if mode == "full":
        values["NvapiPath"] = r".\OptiScaler\fakenvapi.dll"
    for key, value in values.items():
        lines = set_ini_value(lines, key, value)
    return "\n".join(lines).rstrip() + "\n"


def copy_optiscaler_payload(stage: dict, game_dir: Path) -> None:
    dll = Path(stage["dll"])
    ini = Path(stage["ini"])
    release_root = dll.parent
    try:
        shutil.copy2(dll, game_dir / "winmm.dll")
    except OSError as exc:
        raise_if_access_denied(exc, str(game_dir / "winmm.dll"))
    opt_dir = game_dir / "OptiScaler"
    try:
        if opt_dir.exists():
            shutil.rmtree(opt_dir)
        opt_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise_if_access_denied(exc, str(opt_dir))
    for item in release_root.iterdir():
        if item.name in {"OptiScaler.dll", "OptiScaler.ini", "Licenses"}:
            continue
        try:
            if item.is_file() and item.suffix.lower() in {".dll", ".ini"}:
                shutil.copy2(item, opt_dir / item.name)
            elif item.is_dir() and item.name == "D3D12_Optiscaler":
                shutil.copytree(item, opt_dir / item.name)
        except OSError as exc:
            raise_if_access_denied(exc, str(opt_dir / item.name))
    try:
        shutil.copy2(ini, opt_dir / "_source_OptiScaler.ini")
    except OSError as exc:
        raise_if_access_denied(exc, str(opt_dir / "_source_OptiScaler.ini"))


def install_spoof(
    path_value: str,
    *,
    mode: str = "dxgi",
    profile_id: str | None = None,
    close_game: bool = False,
    force_download: bool = False,
) -> dict:
    mode = mode.lower()
    if mode not in {"dxgi", "full"}:
        raise AppError("Invalid mode.")
    running = running_processes()
    if running:
        if not close_game:
            raise AppError("NTE or its launcher is still running. Close it first, or enable the auto-close option.")
        close_game_processes()
    detected = detect_game(path_value)
    win64 = Path(detected["win64"])
    stage = ensure_optiscaler(force_download)
    adapters = get_nvidia_adapters()
    target_device_id = adapters[0].get("DeviceIdHex") if adapters else None
    profile = resolve_profile(profile_id, adapters)

    backup_dir = win64 / BACKUP_DIR_NAME / now_id()
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise_if_access_denied(exc, str(backup_dir))
    manifest = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "tool": "nte-ray-tracing-panel",
        "version": APP_VERSION,
        "mode": mode,
        "profile": profile,
        "win64": str(win64),
        "stage": stage,
        "targetDeviceId": target_device_id,
        "items": [],
        "operations": [],
    }
    for rel in MANAGED_FILES:
        manifest["items"].append(backup_item(win64, rel, backup_dir, kind="file"))
    for rel in MANAGED_DIRS:
        manifest["items"].append(backup_item(win64, rel, backup_dir, kind="dir"))
    manifest["operations"].append("Created pre-install backup")

    copy_optiscaler_payload(stage, win64)
    manifest["operations"].append("Wrote winmm.dll OptiScaler proxy")
    manifest["operations"].append("Wrote OptiScaler dependency directory")
    config = build_optiscaler_config(Path(stage["ini"]), mode=mode, target_device_id=target_device_id, profile=profile, exe_name=detected.get("exeName", GAME_EXE))
    try:
        (win64 / "OptiScaler.ini").write_text(config, encoding="ascii", errors="ignore")
    except OSError as exc:
        raise_if_access_denied(exc, str(win64 / "OptiScaler.ini"))
    manifest["operations"].append(f"Wrote OptiScaler.ini GPU spoof config: {profile['label']}")

    (backup_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "message": "Backup created and ray tracing unlock installed successfully.",
        "backup": str(backup_dir),
        "mode": mode,
        "profile": profile,
        "targetDeviceId": target_device_id,
        "detected": detect_game(path_value),
    }


def restore_backup(path_value: str, backup_id: str | None, *, close_game: bool = False) -> dict:
    running = running_processes()
    if running:
        if not close_game:
            raise AppError("NTE or its launcher is still running. Close it first, or enable the auto-close option.")
        close_game_processes()
    detected = detect_game(path_value)
    win64 = Path(detected["win64"])
    backups = list_backups(win64)
    if not backups:
        raise AppError("No backups found to restore.")
    selected_id = backup_id or backups[0]["id"]
    backup_dir = ensure_under(win64 / BACKUP_DIR_NAME / selected_id, win64 / BACKUP_DIR_NAME)
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.is_file():
        raise AppError("Backup manifest.json not found.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    operations = []
    for record in manifest.get("items", []):
        operations.append(restore_item(win64, backup_dir, record))
    return {
        "ok": True,
        "message": f"Backup {selected_id} restored successfully.",
        "operations": operations,
        "detected": detect_game(path_value),
    }


def api_state(path_value: str | None = None) -> dict:
    common = None
    selected = None
    adapters = get_nvidia_adapters()
    if path_value:
        try:
            selected = detect_game(path_value)
        except AppError as exc:
            selected = {"error": str(exc)}
    if not selected:
        common = detect_common_game()
    return {
        "version": APP_VERSION,
        "name": APP_CN_NAME,
        "fullName": APP_FULL_CN_NAME,
        "englishName": APP_EN_NAME,
        "keywords": APP_SEARCH_KEYWORDS,
        "runDir": str(RUN_DIR),
        "toolsDir": str(TOOLS_DIR),
        "processes": running_processes(),
        "procmon": procmon_filter_state(),
        "nvidia": adapters,
        "profiles": spoof_profiles(adapters),
        "defaultProfile": DEFAULT_PROFILE_ID,
        "optiscaler": find_optiscaler_stage(),
        "commonDetected": common,
        "selectedDetected": selected,
        "defaultGamePath": DEFAULT_GAME_PATH,
    }


def schedule_shutdown(server: ThreadingHTTPServer) -> None:
    def worker() -> None:
        time.sleep(0.35)
        server.shutdown()

    threading.Thread(target=worker, daemon=True).start()


class Handler(BaseHTTPRequestHandler):
    server_version = f"NTERayTracingPanel/{APP_VERSION}"

    def log_message(self, fmt: str, *args: object) -> None:
        safe_log("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def send_json(self, data: object, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise AppError("Invalid request JSON.") from exc

    def handle_error(self, exc: Exception) -> None:
        if isinstance(exc, AppError):
            self.send_json({"ok": False, "error": str(exc)}, exc.status)
        else:
            self.send_json({"ok": False, "error": f"Internal error: {exc}"}, 500)

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/api/state":
                query = parse_qs(parsed.query)
                self.send_json({"ok": True, **api_state(query.get("path", [None])[0])})
                return
            if parsed.path == "/api/log":
                query = parse_qs(parsed.query)
                detected = detect_game(query.get("path", [None])[0])
                log = read_log_summary(Path(detected["win64"]) / "OptiScaler.log")
                self.send_json({"ok": True, "log": log})
                return
            if parsed.path == "/api/download/progress":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                try:
                    while True:
                        snap = DOWNLOAD_PROGRESS.snapshot()
                        payload = json.dumps(snap, ensure_ascii=False)
                        self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        if snap["phase"] in ("done", "error", "idle"):
                            break
                        time.sleep(0.25)
                except Exception:
                    pass
                return
            rel = unquote(parsed.path.lstrip("/")) or "index.html"
            target = (WEB_DIR / rel).resolve()
            if not str(target).startswith(str(WEB_DIR.resolve())) or not target.is_file():
                target = WEB_DIR / "index.html"
            content = target.read_bytes()
            mime = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as exc:
            self.handle_error(exc)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            data = self.read_json()
            if parsed.path == "/api/browse":
                selected = run_folder_dialog()
                self.send_json({"ok": True, "path": selected, "cancelled": selected is None})
                return
            if parsed.path == "/api/detect":
                self.send_json({"ok": True, "detected": detect_game(data.get("path"))})
                return
            if parsed.path == "/api/download":
                force = bool(data.get("force"))
                if DOWNLOAD_PROGRESS.active:
                    self.send_json({"ok": False, "error": "A download is already in progress."}, 409)
                    return
                result_box = {}
                def _run():
                    try:
                        result_box["stage"] = ensure_optiscaler(force)
                    except Exception as exc:
                        result_box["error"] = str(exc)
                t = threading.Thread(target=_run, daemon=True)
                t.start()
                t.join(timeout=2)  # wait up to 2s in case it resolves instantly (cached)
                if "stage" in result_box:
                    self.send_json({"ok": True, "optiscaler": result_box["stage"]})
                elif "error" in result_box:
                    self.send_json({"ok": False, "error": result_box["error"]}, 500)
                else:
                    # Still running — tell the frontend to poll /api/download/progress
                    self.send_json({"ok": True, "downloading": True})
                return
                return
            if parsed.path == "/api/install":
                self.send_json(install_spoof(
                    data.get("path"),
                    mode=data.get("mode") or "dxgi",
                    profile_id=data.get("profile") or data.get("profileId"),
                    close_game=bool(data.get("closeGame")),
                    force_download=bool(data.get("forceDownload")),
                ))
                return
            if parsed.path == "/api/restore":
                self.send_json(restore_backup(
                    data.get("path"),
                    data.get("backup"),
                    close_game=bool(data.get("closeGame")),
                ))
                return
            if parsed.path == "/api/shutdown":
                self.send_json({"ok": True, "message": "Backend is shutting down."})
                schedule_shutdown(self.server)
                return
            raise AppError("Unknown API endpoint.", 404)
        except Exception as exc:
            self.handle_error(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="NTE Ray Tracing Panel")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not WEB_DIR.is_dir():
        safe_log("web directory missing", error=True)
        return 1
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/"
    safe_log(f"NTE Ray Tracing Panel {APP_VERSION} running at {url}")
    if not args.no_browser:
        threading.Timer(0.8, lambda: open_browser_safe(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        safe_log("Stopping...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
