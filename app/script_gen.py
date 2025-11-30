import os
import json
from datetime import datetime
from app.genai_client import client
from app.db import get_db_connection

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")

SCRIPT_PROMPT = """
You are a short-video copywriter. Input: {title}, OP: {op}, top_comments: {comments}. 

Output JSON only with keys:
{{
 "tone": "energetic|funny|informative|dry|sardonic",
 "pacing": "slow|medium|fast",
 "cta": "max 6 words",
 "caption_style": "one of: bold-large / minimal / italic",
 "length_seconds": 30,
 "scenes": [
   {{"text":"caption line here","start":0.0,"duration":5.0,"visual":"suggestion (image/card)"}},
   ...
 ]
}}
If user left creative options blank, decide them automatically based on content. Keep total durations ≈ length_seconds.
"""

def generate_script(post_id):
    canonical_path = os.path.join(WORKSPACE_DIR, "canonical", f"{post_id}.json")
    if not os.path.exists(canonical_path):
        print(f"Canonical file not found: {canonical_path}")
        return

    with open(canonical_path, "r") as f:
        data = json.load(f)

    # Construct prompt
    comments_text = "\n".join([f"- {c['body']}" for c in data['comments'][:5]])
    prompt = SCRIPT_PROMPT.format(
        title=data['title'],
        op=data['op'],
        comments=comments_text
    )
    
    try:
        print(f"Generating script for {post_id}...")
        script_json = client.generate_json(prompt)
        
        # Validate schema (basic check)
        required_keys = ["tone", "pacing", "cta", "scenes"]
        if not all(key in script_json for key in required_keys):
            raise ValueError("Missing required keys in script JSON")
            
        # Save script
        save_script(post_id, script_json)
        print(f"Script generated for {post_id}")
        
    except Exception as e:
        print(f"Error generating script for {post_id}: {e}")

def save_script(post_id, script_data):
    scripts_dir = os.path.join(WORKSPACE_DIR, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    
    file_path = os.path.join(scripts_dir, f"{post_id}.json")
    with open(file_path, "w") as f:
        json.dump(script_data, f, indent=2)
        
    # Update DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO scripts (
            post_id, tone, pacing, cta, caption_style, generated_at, script_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        post_id,
        script_data.get("tone", "neutral"),
        script_data.get("pacing", "medium"),
        script_data.get("cta", ""),
        script_data.get("caption_style", "minimal"),
        datetime.now(),
        json.dumps(script_data)
    ))
    conn.commit()
    conn.close()

def run_script_gen():
    canonical_dir = os.path.join(WORKSPACE_DIR, "canonical")
    if not os.path.exists(canonical_dir):
        print("No canonical directory found.")
        return

    files = [f for f in os.listdir(canonical_dir) if f.endswith(".json")]
    print(f"Generating scripts for {len(files)} files...")
    
    for filename in files:
        post_id = filename.replace(".json", "")
        # Check if already generated? (Optional, skipping for now to allow regeneration)
        generate_script(post_id)

if __name__ == "__main__":
    run_script_gen()
