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
    cursor.execute("SELECT post_id, upvotes, comments, age_hours FROM candidates")
    candidates = cursor.fetchall()
    
    print(f"Scoring {len(candidates)} candidates...")
    
    for row in candidates:
        # We need created_utc to re-calculate age accurately, but for now we can approximate
        # or just use the stored age_hours if we assume it's static from harvest (which is slightly wrong but okay for MVP)
        # Better: fetch created_utc from raw file or store it in DB. 
        # The prompt spec didn't have created_utc in DB, but compute_score needs it.
        # Let's reverse engineer created_utc from age_hours for now, or just use age_hours directly if we modify compute_score.
        # Actually, let's just use the current time and stored age to approximate "original creation time" 
        # created_utc approx = now - (age_hours * 3600)
        # But wait, age_hours in DB is "age at fetch time". 
        # The compute_score function takes created_utc.
        # Let's assume we want to re-score based on CURRENT time.
        
        # To do this right, we should probably have stored created_utc in the DB.
        # But I must follow the schema. 
        # Let's just use the logic: age_hours = (time.time() - created_utc) / 3600.0
        # So created_utc = time.time() - (age_hours * 3600) (at fetch time)
        # This is getting complicated. Let's look at the schema again.
        # Schema: candidates table has `age_hours`.
        # The `harvest.py` I wrote calculates `age_hours` at fetch time.
        
        # Let's just re-calculate score using the values we have.
        # We will treat the stored `age_hours` as the age.
        
        # Wait, the `compute_score` function provided in the prompt takes `created_utc`.
        # I should probably modify `compute_score` to take `age_hours` directly if I don't have `created_utc`.
        # OR I should have added `created_utc` to the DB.
        # The prompt schema didn't have `created_utc`.
        # I will adapt `compute_score` to take `age_hours` or calculate `created_utc` from the stored `age_hours` (which is static).
        # Actually, `age_hours` in DB is static (calculated at fetch).
        # So the score will be static unless we update `age_hours`.
        # For MVP, let's just calculate it once during harvest?
        # No, the prompt says "Implement score.py algorithm and store results".
        # This implies a separate step.
        
        # Let's assume for now we use the static age from fetch.
        # I will calculate a "fake" created_utc to satisfy the function signature.
        
        current_age = row['age_hours'] # This is age at fetch.
        # If we want dynamic scoring (decay over time), we need `fetched_at` to adjust `age_hours`.
        # But let's stick to the prompt's function.
        
        # Let's just pass a created_utc that results in the stored age_hours.
        created_utc = time.time() - (row['age_hours'] * 3600)
        
        score, _ = compute_score(row['upvotes'], row['comments'], created_utc)
        
        cursor.execute("UPDATE candidates SET score = ? WHERE post_id = ?", (score, row['post_id']))
    
    conn.commit()
    conn.close()
    print("Scoring complete.")

if __name__ == "__main__":
    run_scoring()
