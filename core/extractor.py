import re
from typing import Dict, Any, List, Optional
import yt_dlp
from core.utils import logger, format_bytes


class ExtractionError(Exception):
    """Custom exception for metadata extraction failures."""
    pass


def validate_youtube_url(url: str) -> bool:
    """Validate YouTube URL format using robust regex pattern."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    youtube_regex = (
        r'^(https?://)?(www\.|m\.)?'
        r'(youtube\.com/(watch\?.*v=|shorts/|v/|embed/)|youtu\.be/)'
        r'([a-zA-Z0-9_-]{11})'
    )
    return bool(re.search(youtube_regex, url))


def extract_video_info(url: str) -> Dict[str, Any]:
    """Retrieve YouTube metadata WITHOUT downloading media.
    
    Returns clean dictionary containing metadata and format information.
    Raises ExtractionError on failure with clean user-facing error message.
    """
    if not validate_youtube_url(url):
        raise ExtractionError("Invalid YouTube URL. Please enter a valid video or shorts link.")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
        'no_color': True,
    }

    try:
        logger.info(f"Extracting metadata for URL: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False)
            
            if not info:
                raise ExtractionError("Unable to retrieve video information.")
                
            # If the URL is a playlist or multi-video, extract the first entry
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            formats = info.get("formats", [])

            metadata = {
                "id": info.get("id"),
                "title": info.get("title", "Untitled Video"),
                "uploader": info.get("uploader") or info.get("channel") or "Unknown Uploader",
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "upload_date": info.get("upload_date"),
                "view_count": info.get("view_count"),
                "formats": formats,
                "video_options": parse_video_formats(formats),
                "audio_options": parse_audio_formats(formats),
                "webpage_url": info.get("webpage_url", url),
            }
            logger.info(f"Successfully extracted info for: '{metadata['title']}' ({metadata['id']})")
            return metadata

    except yt_dlp.utils.DownloadError as de:
        err_str = str(de).lower()
        logger.error(f"yt-dlp DownloadError for {url}: {de}")
        
        if "private video" in err_str:
            raise ExtractionError("This video is private and cannot be accessed.")
        elif "video unavailable" in err_str or "deleted" in err_str:
            raise ExtractionError("This video is unavailable or has been deleted.")
        elif "members-only" in err_str or "paywall" in err_str or "sign in" in err_str:
            raise ExtractionError("This video requires sign-in, membership, or special access.")
        elif "copyright" in err_str:
            raise ExtractionError("This video is unavailable due to copyright restriction.")
        else:
            raise ExtractionError("Unable to access this video. It may be restricted, private, or unavailable.")

    except Exception as e:
        logger.exception(f"Unexpected error during metadata extraction for {url}")
        raise ExtractionError("An unexpected error occurred while fetching video details.")


def parse_video_formats(formats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter and group video formats by resolution height."""
    video_formats = []
    
    # Filter formats that have a video stream
    raw_video = [
        f for f in formats 
        if f.get("vcodec") != "none" and f.get("height") is not None and f.get("height") > 0
    ]
    
    if not raw_video:
        return []

    # Group by height (e.g. 2160, 1440, 1080, 720, 480, 360, 240, 144)
    heights = sorted(list(set(f["height"] for f in raw_video)), reverse=True)
    
    for h in heights:
        h_formats = [f for f in raw_video if f.get("height") == h]
        
        # Sort formats: prefer mp4 container, higher fps, higher filesize/tbr
        def sort_key(f):
            ext_score = 2 if f.get("ext") == "mp4" else 1
            fps = f.get("fps") or 0
            size = f.get("filesize") or f.get("filesize_approx") or f.get("tbr") or 0
            has_audio_score = 1 if f.get("acodec") != "none" else 0
            return (fps, ext_score, size, has_audio_score)
            
        sorted_h = sorted(h_formats, key=sort_key, reverse=True)
        best_f = sorted_h[0]
        
        has_audio = (best_f.get("acodec") != "none")
        fps = best_f.get("fps")
        ext = (best_f.get("ext") or "mp4").upper()
        
        filesize = best_f.get("filesize") or best_f.get("filesize_approx")
        size_str = format_bytes(filesize) if filesize else "Size ~N/A"
        
        res_label = f"{h}p"
        if fps and fps >= 50:
            res_label += f" {int(fps)}fps"

        audio_info = "Includes Audio" if has_audio else "FFmpeg Audio Merge"
        
        label = f"{res_label} ({ext}) • {size_str} • [{audio_info}]"
        
        video_formats.append({
            "format_id": best_f.get("format_id"),
            "height": h,
            "resolution": res_label,
            "fps": fps,
            "ext": (best_f.get("ext") or "mp4").lower(),
            "has_audio": has_audio,
            "filesize": filesize,
            "label": label,
            "raw_format": best_f
        })
        
    return video_formats


def parse_audio_formats(formats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse audio options for Audio Only downloads."""
    raw_audio = [
        f for f in formats 
        if f.get("acodec") != "none" and (f.get("vcodec") == "none" or f.get("height") is None)
    ]
    
    best_raw_size = None
    if raw_audio:
        sizes = [f.get("filesize") or f.get("filesize_approx") for f in raw_audio if (f.get("filesize") or f.get("filesize_approx"))]
        if sizes:
            best_raw_size = max(sizes)
            
    size_approx_str = f" (~{format_bytes(best_raw_size)})" if best_raw_size else ""
    
    audio_options = [
        {
            "format_id": "bestaudio",
            "audio_mode": "mp3",
            "quality": "320",
            "label": f"MP3 • Best Quality (320 kbps){size_approx_str}",
            "ext": "mp3"
        },
        {
            "format_id": "bestaudio",
            "audio_mode": "mp3",
            "quality": "256",
            "label": f"MP3 • High Quality (256 kbps){size_approx_str}",
            "ext": "mp3"
        },
        {
            "format_id": "bestaudio",
            "audio_mode": "mp3",
            "quality": "128",
            "label": f"MP3 • Standard Quality (128 kbps){size_approx_str}",
            "ext": "mp3"
        },
        {
            "format_id": "bestaudio",
            "audio_mode": "m4a",
            "quality": "best",
            "label": f"M4A / AAC • Native Audio Stream{size_approx_str}",
            "ext": "m4a"
        },
        {
            "format_id": "bestaudio",
            "audio_mode": "opus",
            "quality": "best",
            "label": f"OPUS • High Efficiency Stream{size_approx_str}",
            "ext": "opus"
        }
    ]
    
    return audio_options
