import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "/data/app.db")

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database with the required schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Candidates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        post_id TEXT PRIMARY KEY,
        subreddit TEXT,
        title TEXT,
        op TEXT,
        upvotes INTEGER,
        comments INTEGER,
        fetched_at TIMESTAMP,
        age_hours REAL,
        score REAL,
        raw_path TEXT
    );
    """)
    
    # Scripts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scripts (
        post_id TEXT PRIMARY KEY,
        tone TEXT,
        pacing TEXT,
        cta TEXT,
        caption_style TEXT,
        generated_at TIMESTAMP,
        script_json TEXT
    );
    """)
    
    # Flagged table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flagged (
        post_id TEXT PRIMARY KEY,
        reason TEXT,
        flagged_at TIMESTAMP,
        data_path TEXT
    );
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
