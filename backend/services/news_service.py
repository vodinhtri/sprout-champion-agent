import feedparser
from typing import List, Dict

RSS_FEEDS = {
    "general":      "https://vnexpress.net/rss/tin-moi-nhat.rss",
    "finance":      "https://vnexpress.net/rss/kinh-doanh.rss",
    "world":        "https://vnexpress.net/rss/the-gioi.rss",
    "tech":         "https://vnexpress.net/rss/so-hoa.rss",
    "sports":       "https://vnexpress.net/rss/the-thao.rss",
    "entertainment":"https://vnexpress.net/rss/giai-tri.rss",
    "cafef":        "https://cafef.vn/thi-truong-chung-khoan.rss",
    "lifestyle":    "https://vnexpress.net/rss/suc-khoe.rss",
}

INTEREST_TO_FEEDS = {
    "finance":      ["finance", "cafef"],
    "news":         ["general"],
    "world":        ["world"],
    "tech":         ["tech"],
    "sports":       ["sports"],
    "entertainment":["entertainment"],
    "lifestyle":    ["lifestyle"],
    "work":         ["tech", "general"],
}


async def get_news(interests: List[str]) -> List[Dict]:
    feed_keys = set()
    for interest in interests:
        feed_keys.update(INTEREST_TO_FEEDS.get(interest, ["general"]))

    if not feed_keys:
        feed_keys = {"general"}

    articles = []
    for key in list(feed_keys)[:5]:
        url = RSS_FEEDS.get(key)
        if not url:
            continue
        try:
            feed = feedparser.parse(url)
            source_title = feed.feed.get("title", key)
            for entry in feed.entries[:5]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                # Strip HTML tags simply
                import re
                summary = re.sub(r"<[^>]+>", "", summary)[:200]
                if title:
                    articles.append({
                        "title": title,
                        "summary": summary,
                        "source": source_title,
                        "link": entry.get("link", "").strip(),
                    })
        except Exception as e:
            print(f"[news] RSS error {key}: {e}")

    return articles[:20]
