import os
import json
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")

def create_card(text, output_path, width=1080, height=1920):
    """Creates a simple text card."""
    img = Image.new('RGB', (width, height), color=(30, 30, 30))
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
    
    for line in lines:
        # d.textbbox is better but let's stick to simple for now or use textlength
        # d.text((x, y), line, font=font, fill=(255, 255, 255), anchor="mm") 
        # anchor="mm" centers it at x,y. 
        d.text((width/2, y), line, font=font, fill=(255, 255, 255), anchor="mm")
        y += line_height
        
    img.save(output_path)

def generate_video(post_id):
    scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
    output_dir = os.path.join(WORKSPACE_DIR, "output")
    script_path = os.path.join(scripts_dir, f"{post_id}.json")
    audio_path = os.path.join(output_dir, f"{post_id}.wav")
    
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        return
    if not os.path.exists(audio_path):
        print(f"Audio not found: {audio_path}")
        return

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
        # Actually, if video is defined by duration, it might be shorter/longer than audio.
        # If we want to match audio, we should ensure video is long enough.
        # But -shortest is good practice if we want to clip silence or extra frames.
        output_video_path
    ]
    
    print(f"Rendering video for {post_id}...")
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Video saved to {output_video_path}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")

def run_render():
    scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
    if not os.path.exists(scripts_dir):
        print("No scripts directory found.")
        return

    files = [f for f in os.listdir(scripts_dir) if f.endswith(".json")]
    print(f"Rendering {len(files)} videos...")
    
    for filename in files:
        post_id = filename.replace(".json", "")
        generate_video(post_id)

if __name__ == "__main__":
    run_render()
