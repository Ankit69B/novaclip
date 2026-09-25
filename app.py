import sys
import os
from pathlib import Path

# Guarantee project root directory is in sys.path for Streamlit Cloud deployment
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from ui.styles import apply_custom_css
from core.utils import (
    format_duration,
    format_views,
    format_upload_date,
    format_bytes,
    logger,
    get_system_diagnostics,
    get_base_ytdlp_opts
)
from core.extractor import validate_youtube_url, extract_video_info, ExtractionError
from core.downloader import download_media, DownloadError

# Default download directory
DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")

# Page configuration
st.set_page_config(
    page_title="NovaClip",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Apply Glassmorphism Dark Theme
apply_custom_css()

# Session state initialization
if "metadata" not in st.session_state:
    st.session_state["metadata"] = None
if "current_url" not in st.session_state:
    st.session_state["current_url"] = ""

# Header Card Component
st.markdown(
    """
    <div class="header-container">
        <div class="badge-pill">⚡ AD-FREE MEDIA EXTRACTOR</div>
        <h1 class="brand-title">NOVACLIP</h1>
        <p class="app-desc">
            Fast and clean YouTube downloader. Inspect resolutions, check estimated file sizes, and extract high-definition media.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# URL Input Component
url_input = st.text_input(
    label="YouTube URL Input",
    placeholder="Paste YouTube video or shorts link here...",
    key="yt_url_input",
    label_visibility="collapsed"
)

col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    analyze_btn = st.button("Analyze Video", type="primary", use_container_width=True)
with col_btn2:
    if st.button("Clear", use_container_width=True):
        st.session_state["metadata"] = None
        st.session_state["current_url"] = ""
        st.rerun()

# Trigger metadata analysis when requested
if analyze_btn:
    url_stripped = url_input.strip()
    if not url_stripped:
        st.warning("Please enter a YouTube video URL.")
    elif not validate_youtube_url(url_stripped):
        st.error("Please enter a valid YouTube URL (e.g., https://www.youtube.com/watch?v=... or https://youtu.be/...)")
    else:
        with st.spinner("Extracting video metadata..."):
            try:
                metadata = extract_video_info(url_stripped)
                st.session_state["metadata"] = metadata
                st.session_state["current_url"] = url_stripped
            except ExtractionError as ee:
                st.session_state["metadata"] = None
                st.error(str(ee))
            except Exception as e:
                st.session_state["metadata"] = None
                logger.exception("Unexpected error in UI metadata analysis")
                st.error("Unable to access this video. It may be private or restricted.")

# Display Extracted Media Details & Download Controls
if st.session_state["metadata"]:
    meta = st.session_state["metadata"]
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Thumbnail & Title Presentation
    if meta.get("thumbnail"):
        st.image(meta["thumbnail"], use_container_width=True)

    st.markdown(f"<h3 style='text-align: center; font-weight: 700; margin-top: 1rem; color: #ffffff;'>{meta.get('title', 'Untitled')}</h3>", unsafe_allow_html=True)
    
    # Symmetrical Info Grid
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.markdown(f"<div class='info-card'>📺 <b>Channel:</b> {meta.get('uploader', 'Unknown')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='info-card'>⏱ <b>Duration:</b> {format_duration(meta.get('duration'))}</div>", unsafe_allow_html=True)
    with info_col2:
        st.markdown(f"<div class='info-card'>📅 <b>Uploaded:</b> {format_upload_date(meta.get('upload_date'))}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='info-card'>👁 <b>Views:</b> {format_views(meta.get('view_count'))}</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Format Options Grid
    opt_col1, opt_col2 = st.columns(2)
    
    with opt_col1:
        download_type_str = st.selectbox(
            "Download Mode",
            options=["Video (with Audio)", "Audio Only"],
            key="download_type_select"
        )
    
    is_video_mode = "Video" in download_type_str
    download_type_code = "video" if is_video_mode else "audio"

    selected_format = None
    container_pref = "mp4"

    with opt_col2:
        if is_video_mode:
            video_opts = meta.get("video_options", [])
            if video_opts:
                labels = []
                for opt in video_opts:
                    res = opt['resolution']
                    ext = opt['ext'].upper()
                    size_str = format_bytes(opt['filesize']) if opt.get('filesize') else "Size ~N/A"
                    labels.append(f"{res} ({ext}) • {size_str}")
                    
                selected_idx = st.selectbox(
                    "Quality & File Size",
                    options=range(len(labels)),
                    format_func=lambda i: labels[i],
                    key="video_quality_select"
                )
                selected_format = video_opts[selected_idx]
                container_pref = selected_format.get("ext", "mp4")
            else:
                st.warning("No video formats available.")
        else:
            audio_opts = meta.get("audio_options", [])
            labels = []
            for opt in audio_opts:
                labels.append(opt.get("label", f"{opt['ext'].upper()} {opt['quality']} kbps"))

            selected_idx = st.selectbox(
                "Audio Quality & File Size",
                options=range(len(labels)),
                format_func=lambda i: labels[i],
                key="audio_quality_select"
            )
            selected_format = audio_opts[selected_idx]

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Download Trigger Button
    if st.button("🚀 Download Media", type="primary", use_container_width=True, key="start_download_btn"):
        if not selected_format:
            st.error("Please select a media format.")
        else:
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            stats_cols = st.empty()
            
            def ui_progress_callback(pdata: dict):
                pct = pdata.get("percent", 0.0)
                progress_bar.progress(float(pct) / 100.0)
                
                if pdata.get("status") == "downloading":
                    status_text.markdown(f"<p style='text-align: center; color: #c084fc; font-weight: 600;'>Downloading {pct:.1f}%</p>", unsafe_allow_html=True)
                    with stats_cols.container():
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Size", f"{pdata.get('downloaded_str')} / {pdata.get('total_str')}")
                        c2.metric("Speed", pdata.get('speed_str'))
                        c3.metric("ETA", pdata.get('eta_str'))
                elif pdata.get("status") == "finished":
                    status_text.markdown("<p style='text-align: center; color: #c084fc; font-weight: 600;'>Merging streams via FFmpeg...</p>", unsafe_allow_html=True)

            try:
                result = download_media(
                    url=st.session_state["current_url"],
                    output_dir=DEFAULT_DOWNLOAD_DIR,
                    download_type=download_type_code,
                    selected_format=selected_format,
                    container_pref=container_pref,
                    progress_callback=ui_progress_callback
                )
                
                progress_bar.progress(1.0)
                status_text.empty()
                stats_cols.empty()
                
                st.balloons()
                st.success("🎉 Download completed successfully!")

                file_ext = Path(result['filepath']).suffix.lower()
                mime_types = {
                    ".mp4": "video/mp4",
                    ".mkv": "video/x-matroska",
                    ".webm": "video/webm",
                    ".mp3": "audio/mpeg",
                    ".m4a": "audio/mp4",
                    ".opus": "audio/opus",
                    ".ogg": "audio/ogg",
                    ".wav": "audio/wav"
                }
                mime_type = mime_types.get(file_ext, "application/octet-stream")

                with open(result['filepath'], "rb") as file_data:
                    st.download_button(
                        label=f"💾 Save '{result['filename']}' ({result['filesize']})",
                        data=file_data,
                        file_name=result['filename'],
                        mime=mime_type,
                        type="primary",
                        use_container_width=True
                    )

            except DownloadError as de:
                progress_bar.empty()
                status_text.empty()
                stats_cols.empty()
                st.error(str(de))
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                stats_cols.empty()
                logger.exception("Unexpected error in download action")
                st.error("An error occurred during media download.")

# Developer System Diagnostics Component
with st.expander("🔧 Developer System Diagnostics", expanded=False):
    diag = get_system_diagnostics()
    st.write(f"**Python Version:** `{diag['python_version']}`")
    st.write(f"**yt-dlp Version:** `{diag['ytdlp_version']}`")
    st.write(f"**FFmpeg Status:** `{diag['ffmpeg_status']}`")
    st.write(f"**FFmpeg Path:** `{diag['ffmpeg_path']}`")
    st.write(f"**OS Platform:** `{diag['os_platform']}`")
    st.write(f"**Streamlit Cloud:** `{'Yes' if diag['is_streamlit_cloud'] else 'No (Local PC)'}`")
    
    # Engine configuration verification
    shared_opts = get_base_ytdlp_opts()
    st.write("**Engine Opts Shared:** `Yes` (Extractor & Downloader synchronized)")
