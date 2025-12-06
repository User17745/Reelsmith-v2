import os
import praw
import sys

# Read from env vars directly to see what Docker sees
print("--- Environment Variables ---")
client_id = os.getenv("REDDIT_CLIENT_ID")
client_secret = os.getenv("REDDIT_CLIENT_SECRET")
user_agent = os.getenv("REDDIT_USER_AGENT")

print(f"REDDIT_CLIENT_ID: '{client_id}'")
print(f"REDDIT_CLIENT_SECRET: '{client_secret}'" + (" (masked)" if client_secret else ""))
print(f"REDDIT_USER_AGENT: '{user_agent}'")

if not client_id or not client_secret or not user_agent:
    print("ERROR: Missing one or more credentials!")
    sys.exit(1)

print("\n--- Testing Connection ---")
try:
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    print(f"Read only: {reddit.read_only}")
    print("Fetching 'python' subreddit...")
    for submission in reddit.subreddit("python").hot(limit=1):
        print(f"Success! Found post: {submission.title}")
    
    # Try to access user info if not read only? (Actually client creds are usually read only for public data but still need valid auth)
    # But usually app credentials work for read-only public access.
    
except Exception as e:
    print(f"Connection FAILED: {e}")
    # Print detailed info if available
    if hasattr(e, 'response'):
        print(f"Response: {e.response}")
