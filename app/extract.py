import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")

def sanitize_text(text):
    """
    Removes URLs, emails, and phone numbers from text.
    Keeps usernames and basic punctuation.
    """
    if not text:
        return ""
        
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[link removed]', text)
    
    # Remove Emails (simple regex)
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[email removed]', text)
    
    # Remove Phone numbers (simple regex, can be tricky)
    # Matches patterns like 123-456-7890, (123) 456-7890
    text = re.sub(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[phone removed]', text)
    
    return text.strip()

def extract_canonical(post_id, workspace_dir=WORKSPACE_DIR):
    """
    Reads raw JSON, sanitizes content, and writes canonical JSON.
    """
    raw_path = os.path.join(workspace_dir, "raw", f"{post_id}.json")
    if not os.path.exists(raw_path):
        print(f"Raw file not found: {raw_path}")
        return None
        
    with open(raw_path, "r") as f:
        raw_data = json.load(f)
        
    canonical_data = {
        "id": raw_data["id"],
        "subreddit": raw_data["subreddit"],
        "title": sanitize_text(raw_data["title"]),
        "op": raw_data["author"], # Keep username
        "selftext": sanitize_text(raw_data.get("selftext", "")),
        "comments": []
    }
    
    # Process comments
    if "comments_data" in raw_data:
        for comment in raw_data["comments_data"]:
            canonical_data["comments"].append({
                "author": comment["author"],
                "body": sanitize_text(comment["body"]),
                "score": comment["score"]
            })
            
    # Write canonical file
    canonical_dir = os.path.join(workspace_dir, "canonical")
    os.makedirs(canonical_dir, exist_ok=True)
    canonical_path = os.path.join(canonical_dir, f"{post_id}.json")
    
    with open(canonical_path, "w") as f:
        json.dump(canonical_data, f, indent=2)
        
    return canonical_path

def run_extraction():
    """Iterates over all raw files and creates canonical versions."""
    raw_dir = os.path.join(WORKSPACE_DIR, "raw")
    if not os.path.exists(raw_dir):
        print("No raw directory found.")
        return

    files = [f for f in os.listdir(raw_dir) if f.endswith(".json")]
    print(f"Extracting {len(files)} files...")
    
    for filename in files:
        post_id = filename.replace(".json", "")
        try:
            path = extract_canonical(post_id)
            if path:
                print(f"Extracted {post_id} -> {path}")
        except Exception as e:
            print(f"Error extracting {post_id}: {e}")

if __name__ == "__main__":
    run_extraction()
