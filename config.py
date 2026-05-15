import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

GMAIL_SENDER = os.getenv("GMAIL_SENDER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT")

SUBREDDITS = [s.strip() for s in os.getenv("SUBREDDITS", "TheRaceTo10Million,stocks,ValueInvesting").split(",")]
POSTS_PER_SUBREDDIT = int(os.getenv("POSTS_PER_SUBREDDIT") or "10")
TOP_COMMENTS_COUNT = int(os.getenv("TOP_COMMENTS_COUNT") or "3")
DIGEST_MODE = os.getenv("DIGEST_MODE", "daily")  # "daily" ou "weekly"


def validate():
    required = {
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
        "GMAIL_SENDER": GMAIL_SENDER,
        "GMAIL_APP_PASSWORD": GMAIL_APP_PASSWORD,
        "GMAIL_RECIPIENT": GMAIL_RECIPIENT,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise EnvironmentError(f"Variáveis de ambiente em falta: {', '.join(missing)}")
