# YouTube Live Stream Generator (Slides + Music)

Generates a 1080p YouTube Live stream from a CSV of people (rank, name, image).  
Each entry renders as a full‑screen slide with optional background music, smooth crossfades, automatic resume after crashes, and basic logging.

---

## Features

- 1080p @ 30fps H.264 video with AAC audio (YouTube‑friendly defaults)
- Crossfade transitions between slides
- Auto‑resume from the last streamed rank (`last_rank.txt`)
- Simple asset structure (font, CSV, music)
- Works on Windows, macOS, and Linux (desktop or headless server)

---

## Repo Structure (suggested)

```
.
├─ youtube_stream_script.py        # Main script (yours)
├─ requirements.txt                # Python deps
├─ assets/
│  ├─ font.ttf                     # Display font (provide your own)
│  ├─ final_ranks.csv              # Data source (see format below)
│  └─ background_music.mp3         # Looping background track (optional)
├─ last_rank.txt                   # Auto-created checkpoint (do not commit)
├─ stream_crash.log                # Auto-created by the script
└─ crash_history.log               # Auto-created by the script
```

> If you prefer the filename `youtube_stream_script.py`, rename the script or adjust the commands accordingly.

---

## Requirements

- **Python** 3.9+ (recommend 3.10+)
- **FFmpeg** installed and available on `PATH`
  - Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows:
    - via winget: `winget install Gyan.FFmpeg`  
      or via Chocolatey: `choco install ffmpeg`  
      or download a static build and add its `bin` to PATH
- **Python packages** (install with `pip`):
  - `pillow`
  - `pandas`
  - `requests`

A sample `requirements.txt`:
```
pillow
pandas
requests
```

---

## Data (CSV) Format

Place your CSV at `assets/final_ranks.csv` with these columns:

- `Final_Rank` (integer)
- `Name` (string)
- `Image` (URL to an image; JPEG/PNG recommended)

**Encoding:** If your CSV is UTF‑8 and you see garbled characters, change the `pd.read_csv` call’s `encoding` parameter to `utf-8` or re-save the CSV accordingly.

---

## Configuration

Open the script and review the configuration block near the top. You’ll see variables like:

```python
WIDTH, HEIGHT = 1920, 1080
FONT_PATH = "assets/font.ttf"        # Make sure this exists
FONT_SIZE = 80
COLOR_HEX = "#104080"
CSV_PATH = "assets/final_ranks.csv"  # Make sure this exists
# DURATION, CROSSFADE_DURATION, and FFmpeg settings are defined below in the script
# Make sure your YouTube RTMP ingest URL + stream key is set where FFmpeg is launched
```

- **YouTube RTMP URL + Stream Key:** Copy from YouTube Live Control Room. Look for where FFmpeg is started in the script and update the RTMP URL there.
- **Fonts & Assets:** Ensure `assets/font.ttf` exists; change `FONT_PATH` if you use a different font.
- **Bitrate/Quality:** Adjust in the FFmpeg launch arguments inside the script.

---

## Installation

### macOS / Linux (Desktop)

```bash
# 1) Clone
git clone <your-repo-url>
cd <your-repo>

# 2) Create & activate a venv
python3 -m venv .venv
source .venv/bin/activate

# 3) Install deps
pip install -r requirements.txt

# 4) Verify ffmpeg
ffmpeg -version
```

### Windows (PowerShell)

```powershell
# 1) Clone
git clone <your-repo-url>
cd <your-repo>

# 2) Create & activate a venv
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3) Install deps
pip install -r requirements.txt

# 4) Verify ffmpeg
ffmpeg -version
```

---

## Running

### Quick Start (Desktop)

```bash
# macOS / Linux
source .venv/bin/activate
python3 youtube_stream_script.py
```

```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
python .\youtube_stream_script.py
```

The script will:
- Sort your CSV by `Final_Rank`,
- Start at the rank stored in `last_rank.txt` (or create it),
- Stream frames to YouTube with crossfades and music,
- Update `last_rank.txt` as it progresses.

**Reset to the top?** Delete `last_rank.txt`.

---

## Headless Server (Auto‑Restart Loop)

Run the loop below to keep the stream alive and auto‑restart on crashes (as requested). 

```bash
while true; do   echo "[Start] $(date)" | tee -a /root/stream.log;   python3 -u youtube_stream_script.py 2>&1 | tee -a /root/stream.log;   echo "[Crash Detected] $(date)" | tee -a /root/stream.log;   echo "[Restarting...]" | tee -a /root/stream.log;   sleep 3; done
```

**Tip:** Run inside `tmux` or `screen` so it survives SSH disconnects.

---

## Troubleshooting

- **`ffmpeg: command not found`** — Install FFmpeg and ensure it’s on PATH.
- **Black screen / No feed on YouTube** — Check the RTMP URL + stream key and that your event is live.
- **`BrokenPipeError` in logs** — FFmpeg likely died. Use the headless loop; inspect `stream.log` and any script logs.
- **Images not loading** — Verify `Image` URLs are reachable and valid.
- **Encoding issues** — Adjust `encoding` in `pd.read_csv` or re-save the CSV.
- **Start over from Rank 1** — Delete `last_rank.txt` before launching.

---

## Notes

- Keep your YouTube **Stream Key** secret. Do not commit it.
- Consider a limited Linux user for running the stream in production.
- Monitor CPU usage; adjust FFmpeg preset/bitrate if needed.

---

## License

MIT (or your preferred license).
