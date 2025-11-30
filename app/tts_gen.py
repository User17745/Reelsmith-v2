import os
import json
import wave
from app.genai_client import client

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")

def generate_tts(post_id):
    scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
    script_path = os.path.join(scripts_dir, f"{post_id}.json")
    
    if not os.path.exists(script_path):
        print(f"Script file not found: {script_path}")
        return

    with open(script_path, "r") as f:
        data = json.load(f)

    # Extract text from scenes
    narration_text = ""
    for scene in data.get("scenes", []):
        if "text" in scene:
            narration_text += f"{scene['text']} "
    
    narration_text = narration_text.strip()
    if not narration_text:
        print(f"No text found in script for {post_id}")
        return

    try:
        print(f"Generating audio for {post_id}...")
        audio_bytes = client.generate_audio(narration_text)
        
        if audio_bytes:
            output_dir = os.path.join(WORKSPACE_DIR, "output")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{post_id}.wav")
            
            # Write WAV file
            # Gemini returns raw PCM (audio/L16;rate=24000)
            with wave.open(output_path, "wb") as wav_file:
                wav_file.setnchannels(1) # Mono
                wav_file.setsampwidth(2) # 16-bit = 2 bytes
                wav_file.setframerate(24000)
                wav_file.writeframes(audio_bytes)
                
            print(f"Audio saved to {output_path}")
        else:
            print(f"Failed to generate audio for {post_id}")
            
    except Exception as e:
        print(f"Error generating TTS for {post_id}: {e}")

def run_tts():
    scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
    if not os.path.exists(scripts_dir):
        print("No scripts directory found.")
        return

    files = [f for f in os.listdir(scripts_dir) if f.endswith(".json")]
    print(f"Generating TTS for {len(files)} files...")
    
    for filename in files:
        post_id = filename.replace(".json", "")
        generate_tts(post_id)

if __name__ == "__main__":
    run_tts()
