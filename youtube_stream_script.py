import subprocess
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import requests
from io import BytesIO
import time
import os
import unicodedata
from datetime import datetime

# === CONFIGURATION ===
WIDTH, HEIGHT = 1920, 1080
FONT_PATH = "assets/font.ttf" # Ensure this font file is available
FONT_SIZE = 80
COLOR_HEX = "#104080"
CSV_PATH = "assets/final_ranks.csv" # Ensure this CSV file is available
MUSIC_PATH = "assets/background_music.mp3" # Ensure this music file is available
FPS = 30
DURATION = 3.5
CROSSFADE_DURATION = 0.5
YOUTUBE_RTMP_URL = "rtmp://a.rtmp.youtube.com/live2/YOUTUBE_STREAM_KEY" # Replace with your actual stream key

# === GLOBAL STATE ===
stream_dead = False
ffmpeg = None
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

# === FUNCTIONS ===
def launch_ffmpeg():
    return subprocess.Popen([
        "ffmpeg",
        "-re",
        "-f", "image2pipe",
        "-framerate", str(FPS),
        "-i", "-",
        "-stream_loop", "-1", "-i", MUSIC_PATH,
        "-c:v", "libx264",
        "-b:v", "6000k",
        "-g", "120",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-f", "flv",
        YOUTUBE_RTMP_URL
    ], stdin=subprocess.PIPE)

def sanitize_text(text):
    try:
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    except:
        return text

def generate_text_slide(text):
    text = sanitize_text(text)
    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_HEX)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text(((WIDTH - bbox[2]) // 2, (HEIGHT - bbox[3]) // 2),
              text, font=font, fill="white", stroke_width=4, stroke_fill="black")
    return img

def generate_slide_image(Final_Rank, name, image_url):
    name = sanitize_text(name)
    canvas = Image.new("RGB", (WIDTH, HEIGHT), COLOR_HEX)
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(image_url, timeout=10, headers=headers)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content)).convert("RGB")
        new_height = HEIGHT
        new_width = int(img.width * (HEIGHT / img.height))
        img = img.resize((new_width, new_height))
        x_offset = (WIDTH - new_width) // 2
        canvas.paste(img, (x_offset, 0))
    except Exception as e:
        print(f"[!] Fallback for Final_Rank {Final_Rank}: {e}")
        return generate_text_slide(f"Number {Final_Rank}\n{name}")

    draw = ImageDraw.Draw(canvas)
    lines = [f"Number {Final_Rank}", name]
    y_offset = (HEIGHT - (len(lines) * FONT_SIZE + 10)) // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        y = y_offset + i * (FONT_SIZE + 10)
        draw.text((x, y), line, font=font, fill="white", stroke_width=2, stroke_fill="black")
    return canvas

def send_slide_to_ffmpeg(image, duration):
    global stream_dead, ffmpeg
    if stream_dead:
        restart_stream()
    buf = BytesIO()
    image.save(buf, format='JPEG')
    frame_data = buf.getvalue()
    for _ in range(round(FPS * duration)):
        try:
            ffmpeg.stdin.write(frame_data)
        except (BrokenPipeError, OSError) as e:
            print(f"[!] Write error: {e}")
            stream_dead = True
            log_crash()
            break

def send_crossfade(from_img, to_img, duration):
    global stream_dead, ffmpeg
    if stream_dead:
        restart_stream()
    steps = int(FPS * duration)
    for i in range(steps):
        alpha = i / steps
        blended = Image.blend(from_img, to_img, alpha)
        buf = BytesIO()
        blended.save(buf, format='JPEG')
        frame_data = buf.getvalue()
        try:
            ffmpeg.stdin.write(frame_data)
        except (BrokenPipeError, OSError) as e:
            print(f"[!] Crossfade write error: {e}")
            stream_dead = True
            log_crash()
            break

def log_crash():
    with open("stream_crash.log", "a") as f:
        f.write(f"[{time.ctime()}] FFmpeg crashed and was marked dead.\n")

def restart_stream():
    global ffmpeg, stream_dead
    print("[!] Restarting FFmpeg stream...")
    try:
        ffmpeg.stdin.close()
        ffmpeg.wait()
    except:
        pass
    ffmpeg = launch_ffmpeg()
    stream_dead = False

# === MAIN SCRIPT ===
df = pd.read_csv(CSV_PATH, encoding='ISO-8859-1')

# Load last processed rank
last_rank_file = "last_rank.txt"
try:
    with open(last_rank_file) as f:
        start_rank = int(f.read().strip())
except FileNotFoundError:
    start_rank = 1252802

df = df.sort_values(by='Final_Rank', ascending=False)

if start_rank < 1252802:
    with open("crash_history.log", "a") as log:
        log.write(f"Recovered at {datetime.now()} from rank {start_rank}\n")

# Filter the DataFrame from the last processed rank
df = df[df['Final_Rank'] <= start_rank].reset_index(drop=True)

ffmpeg = launch_ffmpeg()

if start_rank == 1:
    intro_img = generate_text_slide(f"Top {len(df)} People")
    send_slide_to_ffmpeg(intro_img, DURATION + 10)  # Add 10 second delay for stream stabilization

prev_slide = None
for _, row in df.iterrows():
    if stream_dead:
        break
    rank = row['Final_Rank']
    print(f"Streaming Final_Rank {rank}...")
    slide_img = generate_slide_image(rank, row['Name'], row['Image'])
    if prev_slide:
        send_crossfade(prev_slide, slide_img, CROSSFADE_DURATION)
    send_slide_to_ffmpeg(slide_img, DURATION)
    prev_slide = slide_img

    try:
        with open(last_rank_file, "w") as f:
            f.write(str(rank))
    except Exception as e:
        print(f"[!] Could not write last_rank: {e}")

if not stream_dead:
    outro_img = generate_text_slide("Thanks for Watching")
    send_crossfade(prev_slide, outro_img, CROSSFADE_DURATION)
    send_slide_to_ffmpeg(outro_img, DURATION + 10)
    ffmpeg.stdin.close()
    ffmpeg.wait()
