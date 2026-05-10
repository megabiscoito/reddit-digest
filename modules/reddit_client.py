import time
import requests
from config import POSTS_PER_SUBREDDIT, TOP_COMMENTS_COUNT, DIGEST_MODE

HEADERS = {"User-Agent": "reddit_digest/1.0 (personal digest bot)"}
BASE_URL = "https://www.reddit.com"


def _get(url: str, params: dict = None) -> dict:
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            if attempt == 2:
                raise
            time.sleep(5)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                time.sleep(10)
                continue
            raise


def fetch_subreddit(subreddit_name: str) -> dict:
    if DIGEST_MODE == "weekly":
        endpoint = f"{BASE_URL}/r/{subreddit_name}/top.json"
        params = {"limit": POSTS_PER_SUBREDDIT + 5, "t": "week"}
    else:
        endpoint = f"{BASE_URL}/r/{subreddit_name}/top.json"
        params = {"limit": POSTS_PER_SUBREDDIT + 5, "t": "day"}
    data = _get(endpoint, params=params)
    posts = []

    for child in data["data"]["children"]:
        post = child["data"]
        if post.get("stickied"):
            continue
        if len(posts) >= POSTS_PER_SUBREDDIT:
            break

        comments = []
        if TOP_COMMENTS_COUNT > 0:
            try:
                time.sleep(0.5)
                c_data = _get(
                    f"{BASE_URL}/r/{subreddit_name}/comments/{post['id']}.json",
                    params={"limit": TOP_COMMENTS_COUNT, "depth": 1},
                )
                for child_c in c_data[1]["data"]["children"][:TOP_COMMENTS_COUNT]:
                    body = child_c["data"].get("body", "")
                    if body and body not in ("[deleted]", "[removed]"):
                        comments.append(body[:300])
            except Exception:
                pass

        posts.append({
            "title": post["title"],
            "score": post["score"],
            "url": post.get("url", ""),
            "permalink": f"{BASE_URL}{post['permalink']}",
            "selftext": post.get("selftext", "")[:500],
            "num_comments": post.get("num_comments", 0),
            "flair": post.get("link_flair_text") or "",
            "top_comments": comments,
        })

    return {"subreddit": subreddit_name, "posts": posts}


def fetch_all_subreddits(subreddit_names: list[str]) -> list[dict]:
    results = []
    for name in subreddit_names:
        print(f"  r/{name}...")
        results.append(fetch_subreddit(name))
        time.sleep(1)
    return results
