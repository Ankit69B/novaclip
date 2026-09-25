import logging
import os
import shutil
import sys
import platform
import re
from pathlib import Path
from typing import Optional, Dict, Any
import yt_dlp

# Configure application logging
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("novaclip")


def find_ffmpeg_executable() -> Optional[str]:
    """Locate ffmpeg executable in system PATH or common installation directories."""
    which_path = shutil.which("ffmpeg")
    if which_path:
        return which_path

    # Check WinGet package directory on Windows
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        winget_dir = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
        if winget_dir.exists():
            try:
                for ffmpeg_exe in winget_dir.rglob("ffmpeg.exe"):
                    return str(ffmpeg_exe)
            except Exception as e:
                logger.warning(f"Error scanning WinGet directory for ffmpeg: {e}")

    # Check local project directory
    local_project_bin = Path(__file__).resolve().parent.parent / "ffmpeg.exe"
    if local_project_bin.exists():
        return str(local_project_bin)

    return None


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg executable is present."""
    return find_ffmpeg_executable() is not None


def get_base_ytdlp_opts(extra_opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return standard, clean yt-dlp configuration options shared between extraction and downloading."""
    ffmpeg_exe = find_ffmpeg_executable()
    opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'no_color': True,
    }
    if ffmpeg_exe:
        opts['ffmpeg_location'] = str(Path(ffmpeg_exe).parent)

    if extra_opts:
        opts.update(extra_opts)

    return opts


def get_system_diagnostics() -> Dict[str, Any]:
    """Gather diagnostic info for Developer Mode."""
    ffmpeg_path = find_ffmpeg_executable()
    return {
        "python_version": sys.version.split()[0],
        "ytdlp_version": getattr(yt_dlp.version, "__version__", "Unknown"),
        "ffmpeg_status": "Available" if ffmpeg_path else "Not Found",
        "ffmpeg_path": ffmpeg_path or "N/A",
        "os_platform": f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
        "is_streamlit_cloud": os.environ.get("STREAMLIT_SERVER_PORT") is not None or Path("/app").exists()
    }


def sanitize_filename(filename: str) -> str:
    """Remove Windows/Unix invalid characters from filenames."""
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
    sanitized = "".join(ch for ch in sanitized if ord(ch) >= 32)
    return sanitized.strip()


def format_bytes(bytes_num: float | int | None) -> str:
    """Format bytes count to human-readable string (e.g. 15.4 MB)."""
    if bytes_num is None or bytes_num <= 0:
        return "Unknown size"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"


def format_duration(seconds: int | float | None) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if seconds is None:
        return "Unknown"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_views(views: int | None) -> str:
    """Format view count into readable string."""
    if views is None:
        return "N/A"
    if views >= 1_000_000_000:
        return f"{views / 1_000_000_000:.1f}B views"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M views"
    if views >= 1_000:
        return f"{views / 1_000:.1f}K views"
    return f"{views:,} views"


def format_upload_date(date_str: str | None) -> str:
    """Format YYYYMMDD string to readable date format."""
    if not date_str or len(date_str) != 8:
        return "Unknown date"
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, "%Y%m%d")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return date_str


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from error strings."""
    if not text:
        return ""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])|\[0;\d+m|\[0m')
    return ansi_escape.sub('', text)
