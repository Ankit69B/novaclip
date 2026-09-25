import os
import re
from pathlib import Path
from typing import Dict, Any, Callable, Optional
import yt_dlp
from core.utils import (
    logger,
    sanitize_filename,
    format_bytes,
    format_duration,
    check_ffmpeg_available,
    find_ffmpeg_executable,
    strip_ansi_codes,
    get_base_ytdlp_opts
)


class DownloadError(Exception):
    """Custom exception for download operations."""
    pass


def get_unique_filepath(target_dir: Path, filename: str) -> Path:
    """Ensure unique file path by appending counter if file already exists."""
    base_path = target_dir / filename
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    counter = 1
    
    while True:
        candidate = target_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def download_media(
    url: str,
    output_dir: str,
    download_type: str,  # "video" or "audio"
    selected_format: Dict[str, Any],
    container_pref: str = "mp4",
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """Execute media download using yt-dlp with FFmpeg stream merging and real-time progress reporting.
    
    Uses shared base configuration identical to extraction phase.
    """
    ffmpeg_exe = find_ffmpeg_executable()
    ffmpeg_ready = ffmpeg_exe is not None

    target_path = Path(output_dir).resolve()
    target_path.mkdir(parents=True, exist_ok=True)

    outtmpl = str(target_path / "%(title)s [%(id)s].%(ext)s")

    def progress_hook(d: dict):
        if progress_callback and d.get("status") == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            
            percent = (downloaded / total * 100) if total > 0 else 0
            speed = d.get("speed")
            eta = d.get("eta")

            speed_str = f"{format_bytes(speed)}/s" if speed else "N/A"
            eta_str = format_duration(eta) if eta is not None else "N/A"
            downloaded_str = format_bytes(downloaded)
            total_str = format_bytes(total) if total > 0 else "Unknown"

            progress_data = {
                "percent": min(percent, 100.0),
                "downloaded_str": downloaded_str,
                "total_str": total_str,
                "speed_str": speed_str,
                "eta_str": eta_str,
                "status": "downloading"
            }
            progress_callback(progress_data)
        elif progress_callback and d.get("status") == "finished":
            progress_callback({
                "percent": 100.0,
                "status": "finished",
                "filename": d.get("filename", "")
            })

    # Use shared base ytdlp options to ensure compatibility with metadata phase
    ydl_opts = get_base_ytdlp_opts({
        "outtmpl": outtmpl,
        "progress_hooks": [progress_hook],
    })

    if download_type == "video":
        height = selected_format.get("height")
        fmt_id = selected_format.get("format_id")
        
        # Robust format selection: Prefer compatible MP4/M4A streams
        if height and height > 0:
            if ffmpeg_ready:
                ydl_opts["format"] = f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
            else:
                ydl_opts["format"] = f"best[height<={height}][ext=mp4]/best[height<={height}]/best"
        elif fmt_id:
            ydl_opts["format"] = f"{fmt_id}+bestaudio/best"
        else:
            ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            
        target_ext = container_pref.lower()
        if target_ext in ["mp4", "mkv"]:
            ydl_opts["merge_output_format"] = target_ext
            
    else:  # Audio mode
        ydl_opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
        if ffmpeg_ready:
            audio_mode = selected_format.get("audio_mode", "mp3")
            quality = selected_format.get("quality", "320")
            
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_mode,
                "preferredquality": quality,
            }]

    try:
        logger.info(f"Starting download for {url} into {target_path} (Format: {ydl_opts.get('format')})")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if download_type == "audio" and ffmpeg_ready:
                ext = selected_format.get("audio_mode", "mp3")
                filename = str(Path(filename).with_suffix(f".{ext}"))
            elif "merge_output_format" in ydl_opts:
                ext = ydl_opts["merge_output_format"]
                filename = str(Path(filename).with_suffix(f".{ext}"))

            final_file = Path(filename)
            
            if final_file.exists():
                safe_filepath = get_unique_filepath(target_path, final_file.name)
                if safe_filepath != final_file:
                    os.rename(final_file, safe_filepath)
                    final_file = safe_filepath

            logger.info(f"Download completed successfully: {final_file}")
            return {
                "success": True,
                "filepath": str(final_file),
                "filename": final_file.name,
                "filesize": format_bytes(final_file.stat().st_size) if final_file.exists() else "N/A"
            }

    except yt_dlp.utils.DownloadError as de:
        clean_err = strip_ansi_codes(str(de))
        err_lower = clean_err.lower()
        logger.error(f"Download error: {clean_err}")
        
        # Categorized Error Handling (TASK 6)
        if "403" in err_lower or "forbidden" in err_lower:
            # Fallback format retry
            logger.warning("HTTP 403 encountered, trying generic best format fallback...")
            try:
                fallback_opts = dict(ydl_opts)
                fallback_opts["format"] = "best[ext=mp4]/best"
                with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    final_file = Path(filename)
                    return {
                        "success": True,
                        "filepath": str(final_file),
                        "filename": final_file.name,
                        "filesize": format_bytes(final_file.stat().st_size) if final_file.exists() else "N/A"
                    }
            except Exception as fe:
                logger.error(f"Fallback download also failed: {fe}")
                raise DownloadError("YouTube returned HTTP 403 Forbidden for this media stream on the cloud host. Try selecting a different quality option or audio mode.")

        elif "ffmpeg" in err_lower and ("not found" in err_lower or "installed" in err_lower or "exec" in err_lower):
            raise DownloadError("FFmpeg execution error. FFmpeg is required for merging separate streams.")
        elif "private video" in err_lower:
            raise DownloadError("This video is private and cannot be downloaded.")
        elif "unavailable" in err_lower or "deleted" in err_lower:
            raise DownloadError("This video is unavailable or has been removed.")
        elif "network" in err_lower or "connection" in err_lower or "timed out" in err_lower:
            raise DownloadError("Network error while connecting to YouTube servers.")
        else:
            raise DownloadError(f"Download error: {clean_err}")

    except Exception as e:
        logger.exception("Unexpected error during download")
        raise DownloadError("An unexpected error occurred during media download.")
