import os
import json
import shutil
from datetime import datetime
from app.genai_client import client
from app.db import get_db_connection

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")

MODERATION_PROMPT = """
You are a safety classifier. Given the following content (Reddit post title, OP username, top comments) and the short platform rules for TikTok/Instagram/YouTube, answer in strict JSON: {"flag": true|false, "reasons": ["..."]}. Be conservative — if borderline, flag and give reasons. 

Platform rules: 
- No hate speech or harassment
- No sexually explicit content
- No dangerous activities or self-harm
- No graphic violence
- No illegal goods or services

Content: 
{content}
"""

def moderate_post(post_id):
    canonical_path = os.path.join(WORKSPACE_DIR, "canonical", f"{post_id}.json")
    if not os.path.exists(canonical_path):
        print(f"Canonical file not found: {canonical_path}")
        return

    with open(canonical_path, "r") as f:
        data = json.load(f)

    # Construct content string
    content = f"Title: {data['title']}\nOP: {data['op']}\nSelftext: {data['selftext']}\n"
    for c in data['comments']:
        content += f"Comment: {c['body']}\n"

    prompt = MODERATION_PROMPT.replace("{content}", content)
    
    try:
        print(f"Moderating {post_id}...")
        result = client.generate_json(prompt)
        
        if result.get("flag"):
            print(f"FLAGGED {post_id}: {result['reasons']}")
            flag_post(post_id, result['reasons'], canonical_path)
        else:
            print(f"PASSED {post_id}")
            
    except Exception as e:
        print(f"Error moderating {post_id}: {e}")

def flag_post(post_id, reasons, source_path):
    """Moves flagged content to flagged folder and updates DB."""
    flagged_dir = os.path.join(WORKSPACE_DIR, "flagged")
    os.makedirs(flagged_dir, exist_ok=True)
    
    dest_path = os.path.join(flagged_dir, f"{post_id}.json")
    shutil.move(source_path, dest_path)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO flagged (post_id, reason, flagged_at, data_path)
        VALUES (?, ?, ?, ?)
    """, (post_id, json.dumps(reasons), datetime.now(), dest_path))
    conn.commit()
    conn.close()

def run_moderation():
    canonical_dir = os.path.join(WORKSPACE_DIR, "canonical")
    if not os.path.exists(canonical_dir):
        print("No canonical directory found.")
        return

    files = [f for f in os.listdir(canonical_dir) if f.endswith(".json")]
    print(f"Moderating {len(files)} files...")
    
    for filename in files:
        post_id = filename.replace(".json", "")
        moderate_post(post_id)

if __name__ == "__main__":
    run_moderation()
