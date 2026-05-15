import json
import re
import anthropic
from config import ANTHROPIC_API_KEY
from modules.ticker_extractor import extract_ticker_radar

SYSTEM_PROMPT = """You are an expert investment analyst specialising in Reddit communities.
You identify stocks with asymmetric upside using five specific modes. You receive Reddit posts and generate a detailed report in valid JSON.

## THE FIVE MODES — apply to every stock mentioned across all posts:

MODE 1 — Supply Chain (hidden suppliers of a megatrend)
Signals: small/mid-cap company supplying AI, defence, nuclear, grid, GLP-1, reshoring or space megatrends at tier 2-3 of the supply chain. Not the obvious names — the picks nobody is talking about yet. Market cap typically $100M–$5B.

MODE 2 — Early Detection (small caps off institutional radar)
Signals: market cap $50M–$3B, revenue accelerating QoQ, institutional ownership below 40%, few or no analyst coverage, user explicitly argues strong upside ahead. The stock is being discovered, not already discovered.

MODE 3 — Momentum Ascent (Stage 2 Weinstein confirmed)
Signals: price above 50-day and 200-day moving averages, golden cross present or recent, institutional buying mentioned, strong recent earnings or guidance raise, but still far from 52-week high. Momentum confirmed, upside remaining.

MODE 4 — Cyclical Recovery (large cap at cycle bottom)
Signals: large or mega-cap company near 52-week low, sector in downturn but leading indicators turning (inventory normalisation, margin recovery, order book improving), users arguing the worst is priced in.

MODE 5 — Large Cap Turnaround (recovery technically confirmed)
Signals: market cap $10B+, stock recovering from multi-year lows, revenue growth returning after decline, technical breakout confirmed, new catalyst (new CEO, restructuring, new product cycle, regulatory approval).

---

Respond ONLY with valid JSON using this exact structure (use the subreddit name without "r/" as the key):
{
  "subreddits": {
    "<subreddit_name>": {
      "analysis": "3-4 paragraphs: what is being discussed, why, what patterns emerge, overall sentiment and what it reveals about current market conditions",
      "main_themes": ["theme 1", "theme 2", "theme 3", "theme 4", "theme 5"],
      "trends": ["trend 1", "trend 2", "trend 3", "trend 4"],
      "recurring_questions": ["question 1", "question 2", "question 3"],
      "top_stocks": [
        {"ticker": "TICKER", "company": "Company Name", "mentions": 5, "sentiment": "bullish|bearish|neutral", "reason": "why it is being discussed"}
      ],
      "mode_picks": {
        "modo1_supply_chain": [
          {"ticker": "TICKER", "company": "Company Name", "megatrend": "AI / defence / nuclear / grid / GLP-1 / reshoring / space", "thesis": "why this is a hidden tier-2/3 supplier the market has not priced in yet"}
        ],
        "modo2_early_detection": [
          {"ticker": "TICKER", "company": "Company Name", "thesis": "accelerating fundamentals, off institutional radar — specific evidence from posts"}
        ],
        "modo3_momentum_ascent": [
          {"ticker": "TICKER", "company": "Company Name", "thesis": "Stage 2 confirmed, institutional entering — specific technical or fundamental signal mentioned"}
        ],
        "modo4_recuperacao_ciclica": [
          {"ticker": "TICKER", "company": "Company Name", "thesis": "large cap near cycle bottom, leading indicators turning — specific evidence from posts"}
        ],
        "modo5_large_cap_turnaround": [
          {"ticker": "TICKER", "company": "Company Name", "thesis": "recovery technically confirmed, catalyst identified — specific evidence from posts"}
        ]
      },
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
- mode_picks: only include stocks with explicit evidence in the posts — do not infer or hallucinate. If no stock fits a mode, return an empty array for that mode.
- hidden_gems: only lesser-known stocks (not AAPL/MSFT/NVDA/AMZN) that users explicitly argue have strong upside
- sentiment_stats: score is 0-100 (100 = maximum conviction based on post volume and argument quality)
- Be detailed in analysis paragraphs, concise in array items
- Estimate mention counts from post and comment frequency"""


def _extract_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1)
    return json.loads(text.strip())


def _build_post_lines(data: dict) -> str:
    lines = [f"\n## r/{data['subreddit']}\n"]
    for post in data["posts"]:
        lines.append(f"- [{post['score']} pts] {post['title']}")
        if post["selftext"]:
            lines.append(f"  Texto: {post['selftext']}")
        if post["top_comments"]:
            for i, c in enumerate(post["top_comments"], 1):
                lines.append(f"  Comentário {i}: {c}")
    return "\n".join(lines)


def _analyse_subreddit(client, data: dict) -> dict:
    user_content = "Analisa estes posts do Reddit e gera o resumo JSON:\n" + _build_post_lines(data)
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
        subreddits = result.get("subreddits", {})
        normalised = {
            k.lstrip("r/") if k.startswith("r/") else k: v
            for k, v in subreddits.items()
        }
        return normalised
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"  Erro ao parsear JSON de r/{data['subreddit']}: {e}")
        return {}


def generate_summary(subreddit_data: list[dict]) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    merged_subreddits = {}

    for data in subreddit_data:
        print(f"  A analisar r/{data['subreddit']}...")
        result = _analyse_subreddit(client, data)
        merged_subreddits.update(result)

    # Gerar insights cruzados com base nos resumos já produzidos
    summaries_text = "\n".join(
        f"r/{name}: temas={v.get('main_themes', [])}, sentimento={v.get('sentiment', '')}"
        for name, v in merged_subreddits.items()
    )
    cross_response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": (
            "Com base nestes resumos de subreddits de investimento, gera:\n"
            "1. Uma lista de 3 insights que atravessam múltiplas comunidades\n"
            "2. Uma lista de 4 destaques do dia\n"
            f"\n{summaries_text}\n\n"
            'Responde APENAS em JSON válido: {"cross_subreddit_insights": [...], "weekly_highlights": [...]}'
        )}],
    )
    try:
        cross = _extract_json(cross_response.content[0].text)
    except (json.JSONDecodeError, AttributeError):
        cross = {"cross_subreddit_insights": [], "weekly_highlights": []}

    ticker_radar = extract_ticker_radar(subreddit_data)
    for name, items in ticker_radar.items():
        if name in merged_subreddits:
            merged_subreddits[name]['ticker_radar'] = items

    return {
        "subreddits": merged_subreddits,
        "cross_subreddit_insights": cross.get("cross_subreddit_insights", []),
        "weekly_highlights": cross.get("weekly_highlights", []),
    }
