import os
import json
import subprocess
import textwrap
import logging
import wave
from PIL import Image, ImageDraw, ImageFont

from app.logging_utils import configure_logging, log_event
from app.broll import generate_background_montage
from app.validation import generate_validation_report

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")
configure_logging()
logger = logging.getLogger("reelsmith.render")

def create_card(text, output_path, width=1080, height=1920):
    """Creates a simple text card with transparent background."""
    img = Image.new("RGBA", (width, height), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    
    # Try to load a better font, fallback to default
    try:
        # This path is common in some linux distros, but might fail in slim
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except IOError:
        font = ImageFont.load_default()
        # Default font is very small, but it's a fallback
    
    # Wrap text
    # Estimate chars per line (very rough)
    chars_per_line = 30
    lines = textwrap.wrap(text, width=chars_per_line)

    # Draw text centered
    # Simple vertical centering
    line_height = 70 # approx for 60pt font
    total_height = len(lines) * line_height
    y = (height - total_height) / 2

    # Calculate bounding box for overlay panel
    max_width = 0
    for line in lines:
        bbox = d.textbbox((0, 0), line, font=font)
        max_width = max(max_width, bbox[2] - bbox[0])

    padding_x = 60
    padding_y = 40
    panel_width = min(width - 100, max_width + padding_x * 2)
    panel_height = total_height + padding_y * 2
    panel_x0 = (width - panel_width) / 2
    panel_y0 = (height - panel_height) / 2
    panel_x1 = panel_x0 + panel_width
    panel_y1 = panel_y0 + panel_height
    d.rectangle([panel_x0, panel_y0, panel_x1, panel_y1], fill=(0, 0, 0, 160))

    for line in lines:
        # d.textbbox is better but let's stick to simple for now or use textlength
        # d.text((x, y), line, font=font, fill=(255, 255, 255), anchor="mm") 
        # anchor="mm" centers it at x,y. 
        d.text((width/2, y), line, font=font, fill=(255, 255, 255, 255), anchor="mm")
        y += line_height
        
    img.save(output_path)


def _audio_duration_seconds(audio_path):
    with wave.open(audio_path, "rb") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        return frames / float(rate)


def _build_transition_filters(scene_durations, transition_duration=0.2):
    if not scene_durations:
        return ""
    filters = [f"fade=t=in:st=0:d={transition_duration}:alpha=1"]
    cursor = 0.0
    for index, duration in enumerate(scene_durations):
        cursor += duration
        if index < len(scene_durations) - 1:
            out_start = max(cursor - transition_duration, 0)
            filters.append(f"fade=t=out:st={out_start}:d={transition_duration}:alpha=1")
            filters.append(f"fade=t=in:st={cursor}:d={transition_duration}:alpha=1")
    return ",".join(filters)

def generate_video(post_id):
    scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
    output_dir = os.path.join(WORKSPACE_DIR, "output")
    script_path = os.path.join(scripts_dir, f"{post_id}.json")
    audio_path = os.path.join(output_dir, f"{post_id}.wav")
    
    if not os.path.exists(script_path):
        log_event(logger, "render_missing_script", post_id=post_id, path=script_path)
        return None
    if not os.path.exists(audio_path):
        log_event(logger, "render_missing_audio", post_id=post_id, path=audio_path)
        return None

    with open(script_path, "r") as f:
        data = json.load(f)

    # Create temp dir for frames
    frames_dir = os.path.join(WORKSPACE_DIR, "frames", post_id)
    os.makedirs(frames_dir, exist_ok=True)
    
    concat_list_path = os.path.join(frames_dir, "concat.txt")
    
    with open(concat_list_path, "w") as f:
        for i, scene in enumerate(data.get("scenes", [])):
            text = scene.get("text", "")
            duration = scene.get("duration", 3.0)
            
            image_path = os.path.join(frames_dir, f"scene_{i:03d}.png")
            create_card(text, image_path)
            
            # FFmpeg concat format
            # file 'path'
            # duration 5
            abs_image_path = os.path.abspath(image_path)
            f.write(f"file '{abs_image_path}'\n")
            f.write(f"duration {duration}\n")
        
        # Concat demuxer quirk: last file needs to be repeated or it might be skipped/short
        # But usually just adding the last file again without duration helps, 
        # or just relying on the fact that we have audio.
        # Let's add the last file again to be safe if the audio is longer.
        if data.get("scenes"):
             last_image = os.path.join(frames_dir, f"scene_{len(data['scenes'])-1:03d}.png")
             abs_last_image = os.path.abspath(last_image)
             f.write(f"file '{abs_last_image}'\n")

    # Run FFmpeg
    output_video_path = os.path.join(output_dir, f"{post_id}.mp4")
    subtitle_path = os.path.join(output_dir, f"{post_id}.srt")
    audio_duration = _audio_duration_seconds(audio_path)
    tone = data.get("tone")
    background_path = generate_background_montage(post_id, audio_duration, tone=tone)

    scene_durations = [scene.get("duration", 3.0) for scene in data.get("scenes", [])]
    motion_filter = "zoompan=z='min(1.03,zoom+0.0005)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    transition_filter = _build_transition_filters(scene_durations)
    overlay_filters = ",".join([f for f in [motion_filter, transition_filter] if f])

    if background_path:
        filter_parts = [
            f"[0:v]format=rgba,{overlay_filters}[ov];[1:v][ov]overlay=0:0:format=auto[base]"
        ]
        if os.path.exists(subtitle_path):
            filter_parts.append(f"[base]subtitles={subtitle_path}:force_style='Outline=2,Shadow=1'[vout]")
            video_map = "[vout]"
        else:
            video_map = "[base]"

        filter_complex = ";".join(filter_parts)
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_list_path,
            "-i",
            background_path,
            "-i",
            audio_path,
            "-filter_complex",
            filter_complex,
            "-map",
            video_map,
            "-map",
            "2:a",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            output_video_path,
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y", # Overwrite
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p", # Ensure compatibility
            "-c:a", "aac",
            "-shortest", # Stop when shortest input ends (usually audio or video, whichever is shorter)
            output_video_path
        ]

        if os.path.exists(subtitle_path):
            cmd.insert(-1, "-vf")
            cmd.insert(-1, f"{overlay_filters},subtitles={subtitle_path}:force_style='Outline=2,Shadow=1'")
        else:
            cmd.insert(-1, "-vf")
            cmd.insert(-1, overlay_filters)
    
    log_event(logger, "render_start", post_id=post_id)
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(output_video_path):
            generate_validation_report(post_id)
            log_event(logger, "render_saved", post_id=post_id, path=output_video_path)
            return output_video_path
        log_event(logger, "render_missing_output", post_id=post_id, path=output_video_path)
        return None
    except subprocess.CalledProcessError as e:
        log_event(logger, "render_error", post_id=post_id, error=e.stderr.decode())
        return None

def run_render():
    scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
    if not os.path.exists(scripts_dir):
        log_event(logger, "render_no_scripts_dir", path=scripts_dir)
        return

    files = [f for f in os.listdir(scripts_dir) if f.endswith(".json")]
    log_event(logger, "render_batch_start", count=len(files))
    
    for filename in files:
        post_id = filename.replace(".json", "")
        generate_video(post_id)

if __name__ == "__main__":
    run_render()
