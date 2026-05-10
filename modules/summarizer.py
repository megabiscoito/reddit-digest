import json
import re
import anthropic
from config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """You are an expert analyst specialising in investment communities on Reddit.
You receive Reddit posts and must generate a detailed report in valid JSON.

Respond ONLY with valid JSON using this exact structure (use the subreddit name without "r/" as the key):
{
  "subreddits": {
    "<subreddit_name>": {
      "analysis": "3-4 paragraphs with in-depth analysis: what is being discussed, why, what patterns emerge, overall sentiment and what it reveals about market conditions",
      "main_themes": ["theme 1", "theme 2", "theme 3", "theme 4", "theme 5"],
      "trends": ["trend 1", "trend 2", "trend 3", "trend 4"],
      "recurring_questions": ["question 1", "question 2", "question 3"],
      "top_stocks": [
        {"ticker": "TICKER", "company": "Company Name", "mentions": 5, "sentiment": "bullish|bearish|neutral", "reason": "why it is being discussed"}
      ],
      "hidden_gems": [
        {"ticker": "TICKER", "company": "Company Name", "why_bullish": "detailed explanation of why users believe this stock has high growth potential", "confidence_level": "high|medium|low"}
      ],
      "sentiment_stats": {
        "most_bullish": [{"ticker": "TICKER", "score": 85, "reason": "brief reason"}],
        "most_bearish": [{"ticker": "TICKER", "score": 75, "reason": "brief reason"}]
      },
      "top_posts": [
        {"title": "post title", "why_popular": "reason in 1 sentence", "url": "url"}
      ],
      "sentiment": "bullish|bearish|neutral|mixed"
    }
  },
  "cross_subreddit_insights": ["insight 1", "insight 2", "insight 3"],
  "weekly_highlights": ["highlight 1", "highlight 2", "highlight 3", "highlight 4"]
}

Rules:
- Be detailed in the analysis paragraphs but concise in array items
- hidden_gems: only include lesser-known stocks (not mega-caps like AAPL/MSFT/NVDA) that users explicitly argue have strong upside potential — include their reasoning
- sentiment_stats: score is 0-100 (100 = maximum bullish/bearish confidence based on post volume and conviction)
- Estimate mention counts from post and comment frequency"""


def _extract_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1)
    return json.loads(text.strip())


def generate_summary(subreddit_data: list[dict]) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    lines = []
    for data in subreddit_data:
        lines.append(f"\n## r/{data['subreddit']}\n")
        for post in data["posts"]:
            lines.append(f"- [{post['score']} pts] {post['title']}")
            if post["selftext"]:
                lines.append(f"  Texto: {post['selftext']}")
            if post["top_comments"]:
                for i, c in enumerate(post["top_comments"], 1):
                    lines.append(f"  Comentário {i}: {c}")

    user_content = "Analisa estes posts do Reddit e gera o resumo JSON:\n" + "\n".join(lines)

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=8192,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_content}],
    )

    raw = response.content[0].text
    try:
        result = _extract_json(raw)
        # Normalizar chaves — remover prefixo "r/" se presente
        if "subreddits" in result:
            result["subreddits"] = {
                k.lstrip("r/") if k.startswith("r/") else k: v
                for k, v in result["subreddits"].items()
            }
        return result
    except (json.JSONDecodeError, AttributeError):
        return {"raw_summary": raw, "subreddits": {}, "cross_subreddit_insights": [], "weekly_highlights": []}
