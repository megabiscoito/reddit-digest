import re

_BLACKLIST = {
    'A', 'I', 'AI', 'US', 'UK', 'EU', 'UN', 'OK', 'NO',
    'CEO', 'CFO', 'CTO', 'COO', 'IPO', 'ETF', 'USD', 'EUR', 'GBP',
    'DD', 'ATH', 'EPS', 'PE', 'PEG', 'EV', 'YOY', 'QOQ', 'YTD',
    'ROE', 'ROI', 'FCF', 'EBITDA', 'GAAP',
    'IMO', 'FOMO', 'YOLO', 'TLDR', 'OP', 'OC', 'AMA', 'FAQ', 'PSA',
    'WSB', 'SEC', 'FED', 'GDP', 'CPI', 'PPI', 'ISM',
    'IT', 'TV', 'PC', 'API', 'AR', 'VR', 'ML', 'NLP', 'GPU', 'CPU',
    'NYSE', 'NASDAQ', 'AMEX', 'DOW', 'SP',
    'OR', 'AND', 'NOT', 'FOR', 'THE', 'BUT', 'ALL', 'NEW', 'NOW',
    'NEXT', 'LAST', 'BIG', 'BEST', 'TOP', 'HOT', 'BULL', 'BEAR',
    'LONG', 'SHORT', 'CALL', 'PUT', 'ITM', 'OTM', 'ATM',
    'EDIT', 'NOTE', 'HELP', 'NEED', 'WANT', 'JUST', 'ALSO', 'ONLY',
    'MORE', 'LESS', 'HIGH', 'LOW', 'HOLD', 'SELL', 'BUY', 'SAME',
    'WHAT', 'WHEN', 'HAVE', 'WILL', 'THEY', 'THEN', 'THAT', 'THIS',
    'FROM', 'INTO', 'OVER', 'SOME', 'MANY', 'MOST', 'INFO', 'BOTH',
    'GOOD', 'VERY', 'MUCH', 'EVEN', 'BACK', 'STILL', 'EACH', 'SUCH',
    'WELL', 'BEEN', 'THEM', 'WITH', 'DOES', 'CASH', 'DEBT', 'RATE',
    'RISK', 'IIRC', 'AFAIK', 'LOL', 'OMG', 'WTF', 'TBH', 'FYI',
}


def _extract_tickers(text: str) -> list[str]:
    found = set()
    # $TICKER — forma explícita, mais fiável
    for m in re.finditer(r'\$([A-Z]{1,5})\b', text):
        t = m.group(1)
        if t not in _BLACKLIST:
            found.add(t)
    # Palavras em maiúsculas 2-5 letras sem $
    for m in re.finditer(r'\b([A-Z]{2,5})\b', text):
        t = m.group(1)
        if t not in _BLACKLIST:
            found.add(t)
    return sorted(found)


def extract_ticker_radar(subreddit_data: list[dict]) -> dict[str, list[dict]]:
    """
    Para cada subreddit, encontra posts com 'next' no título
    e extrai todos os tickers mencionados no post e comentários.
    """
    result = {}
    for data in subreddit_data:
        name = data['subreddit']
        items = []
        for post in data['posts']:
            if 'next' not in post['title'].lower():
                continue
            texts = [post.get('selftext', '')]
            texts.extend(post.get('top_comments', []))
            tickers = _extract_tickers(' '.join(texts))
            if tickers:
                items.append({
                    'question': post['title'],
                    'url': post['permalink'],
                    'tickers': tickers,
                })
        if items:
            result[name] = items
    return result
