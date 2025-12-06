
import os
import praw
from dotenv import load_dotenv

load_dotenv()

ID = os.getenv("REDDIT_CLIENT_ID")
SECRET = os.getenv("REDDIT_CLIENT_SECRET")
AGENT = os.getenv("REDDIT_USER_AGENT")

print(f"Testing with: ID={ID}, SECRET={SECRET[:5]}..., AGENT={AGENT}")

try:
    reddit = praw.Reddit(
        client_id=ID,
        client_secret=SECRET,
        user_agent=AGENT
    )
    print("Read only?", reddit.read_only)
    print("User:", reddit.user.me())
except Exception as e:
    print("Error:", e)
