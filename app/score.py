import math
import time
from app.db import get_db_connection

def compute_score(upvotes, comments, created_utc, subreddit_weight=1.0):
    """
    Computes a virality score based on upvotes, comments, and age.
    """
    age_hours = (time.time() - created_utc) / 3600.0
    
    # Avoid log(0)
    s = math.log1p(max(0, upvotes))
    c = math.log1p(max(0, comments))
    
    # Velocity: comments per hour (add 1 to avoid division by zero)
    v = comments / (age_hours + 1)
    
    # Decay factor
    decay = math.exp(-age_hours / 48)
    
    title_boost = 0.4 
    
    score = ((0.65 * s) + (0.25 * c) + (0.4 * v) + title_boost) * decay * subreddit_weight
    return score, age_hours

def run_scoring():
    """Updates scores for all candidates."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all candidates
    cursor.execute("SELECT post_id, upvotes, comments, age_hours, created_utc FROM candidates")
    candidates = cursor.fetchall()
    
    print(f"Scoring {len(candidates)} candidates...")
    
    for row in candidates:
        created_utc = row["created_utc"]
        if not created_utc:
            # Fallback to stored age if available
            stored_age = row["age_hours"]
            if stored_age is None:
                continue
            created_utc = time.time() - (stored_age * 3600)

        score, age_hours = compute_score(row["upvotes"], row["comments"], created_utc)

        cursor.execute(
            "UPDATE candidates SET score = ?, age_hours = ? WHERE post_id = ?",
            (score, age_hours, row["post_id"]),
        )
    
    conn.commit()
    conn.close()
    print("Scoring complete.")

if __name__ == "__main__":
    run_scoring()
