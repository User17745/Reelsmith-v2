import praw
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from app.db import get_db_connection, init_db

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")

def get_reddit_client():
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

def save_raw_post(post, workspace_dir):
    """Saves raw post data to JSON file."""
    raw_dir = os.path.join(workspace_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    post_data = {
        "id": post.id,
        "title": post.title,
        "author": str(post.author),
        "subreddit": str(post.subreddit),
        "score": post.score,
        "num_comments": post.num_comments,
        "created_utc": post.created_utc,
        "url": post.url,
        "selftext": post.selftext,
        "permalink": post.permalink
    }
    
    # Fetch top comments
    post.comments.replace_more(limit=0)
    comments = []
    for comment in post.comments.list()[:10]:
        comments.append({
            "body": comment.body,
            "author": str(comment.author),
            "score": comment.score
        })
    post_data["comments_data"] = comments

    file_path = os.path.join(raw_dir, f"{post.id}.json")
    with open(file_path, "w") as f:
        json.dump(post_data, f, indent=2)
    
    return file_path

def harvest(subreddits=["AskReddit", "Showerthoughts", "LifeProTips"], limit=10):
    """Fetches posts from subreddits and saves them."""
    reddit = get_reddit_client()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"Harvesting from {subreddits}...")
    
    for sub_name in subreddits:
        subreddit = reddit.subreddit(sub_name)
        # Fetch hot and top posts
        for post in list(subreddit.hot(limit=limit)) + list(subreddit.top("day", limit=limit)):
            try:
                # Check if already exists
                cursor.execute("SELECT post_id FROM candidates WHERE post_id = ?", (post.id,))
                if cursor.fetchone():
                    continue
                
                print(f"Processing {post.id}: {post.title[:50]}...")
                
                # Save raw JSON
                raw_path = save_raw_post(post, WORKSPACE_DIR)
                
                # Insert into DB
                cursor.execute("""
                    INSERT INTO candidates (
                        post_id, subreddit, title, op, upvotes, comments, 
                        fetched_at, age_hours, score, raw_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post.id,
                    str(post.subreddit),
                    post.title,
                    str(post.author),
                    post.score,
                    post.num_comments,
                    datetime.now(),
                    (time.time() - post.created_utc) / 3600.0,
                    0.0, # Initial score, will be updated by scorer
                    raw_path
                ))
                conn.commit()
                
            except Exception as e:
                print(f"Error processing {post.id}: {e}")
    
    conn.close()
    print("Harvest complete.")

if __name__ == "__main__":
    init_db()
    harvest()
