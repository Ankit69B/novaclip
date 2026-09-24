# NovaClip ⚡

A premium, ad-free, glassmorphic web application for inspecting and downloading YouTube media. Built using Python 3.11+, Streamlit, `yt-dlp`, and `FFmpeg`.

---

## 🌟 Features

* **Ad-Free & Private**: Zero popups, tracking scripts, or third-party ads.
* **Glassmorphic UI**: Custom dark theme styled with Space Grotesk typography and ambient micro-animations.
* **Metadata Analysis**: Inspect thumbnails, video titles, uploader channels, duration, view counts, and upload dates before downloading.
* **Format & Size Selector**: Displays estimated file sizes next to resolutions (4K, 1080p, 720p, MP3 320kbps).
* **Automatic FFmpeg Stream Merging**: Combines high-resolution video streams with compatible audio streams into clean MP4 or MKV files.
* **Real-time Download Reporting**: Live progress bar, downloaded size, speed, and ETA calculation.
* **Streamlit Cloud Ready**: Pre-configured `packages.txt` for automatic FFmpeg installation on Streamlit Community Cloud.

---

## ⚙️ Local Setup (Windows)

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. FFmpeg Requirement
Ensure FFmpeg is installed on your system (e.g. via `winget install ffmpeg`).

### 3. Run Locally
```powershell
streamlit run app.py
```

---

## 🚀 100% Free Global Deployment on Streamlit Community Cloud

Deploying to **Streamlit Community Cloud** is completely free forever.

### Step-by-Step Instructions:

1. **Push your code to GitHub**:
   - Create a repository on GitHub named `novaclip`.
   - Push all project files (including [`packages.txt`](file:///c:/Users/welome/Desktop/youtbe%20downlad/packages.txt), [`requirements.txt`](file:///c:/Users/welome/Desktop/youtbe%20downlad/requirements.txt), and [`app.py`](file:///c:/Users/welome/Desktop/youtbe%20downlad/app.py)).

2. **Deploy on Streamlit Cloud**:
   - Go to **[share.streamlit.io](https://share.streamlit.io/)**.
   - Sign in with your GitHub account.
   - Click **"New app"** (or **"Deploy an app"**).
   - Choose **"I already have an app"**.
   - Select your Repository: `<your-username>/novaclip`.
   - Branch: `main`.
   - Main file path: `app.py`.
   - Click **"Deploy!"**.

3. **Live Public URL**:
   Streamlit Cloud will read [`packages.txt`](file:///c:/Users/welome/Desktop/youtbe%20downlad/packages.txt), automatically install `ffmpeg`, install Python dependencies, and host your app live at `https://<your-app-name>.streamlit.app`!

---

## ⚖️ Legal & Copyright Note

This application is strictly designed for personal media archival of content you are authorized to download. Please respect copyright laws and YouTube's Terms of Service when using this tool.
