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
    strip_ansi_codes
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
    """Execute media download using yt-dlp with FFmpeg stream merging and real-time progress reporting."""
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

    ydl_opts = {
        "outtmpl": outtmpl,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "no_color": True,
    }

    if ffmpeg_exe:
        ydl_opts["ffmpeg_location"] = str(Path(ffmpeg_exe).parent)

    if download_type == "video":
        fmt_id = selected_format.get("format_id")
        has_audio = selected_format.get("has_audio", False)
        
        if has_audio:
            ydl_opts["format"] = f"{fmt_id}/best"
        else:
            if not ffmpeg_ready:
                ydl_opts["format"] = "best[ext=mp4]/best"
            else:
                ydl_opts["format"] = f"{fmt_id}+bestaudio/bestvideo+bestaudio/best"
            
        target_ext = container_pref.lower()
        if target_ext in ["mp4", "mkv"]:
            ydl_opts["merge_output_format"] = target_ext
            
    else:  # Audio mode
        ydl_opts["format"] = "bestaudio/best"
        if ffmpeg_ready:
            audio_mode = selected_format.get("audio_mode", "mp3")
            quality = selected_format.get("quality", "320")
            
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_mode,
                "preferredquality": quality,
            }]

    try:
        logger.info(f"Starting download for {url} into {target_path} (FFmpeg: {ffmpeg_exe})")
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
        logger.error(f"Download error: {clean_err}")
        
        # Fallback handling
        if "403" in clean_err.lower() or "forbidden" in clean_err.lower() or "sign in" in clean_err.lower():
            logger.warning("Download error encountered, attempting fallback format download...")
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
                raise DownloadError("YouTube restricted this video format. Try selecting a different quality option.")
                
        if "ffmpeg is not installed" in clean_err.lower():
            raise DownloadError(
                "FFmpeg is missing on your system. Please restart your Streamlit app or pick a format marked **[Includes Audio]**."
            )
        raise DownloadError(f"Download failed: {clean_err}")
    except Exception as e:
        logger.exception("Unexpected error during download")
        raise DownloadError("An unexpected error occurred during media download.")
