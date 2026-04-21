"""Pobieranie nagłówków wiadomości z publicznego kanału RSS Google News (bez klucza API)."""

from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


def fetch_google_news_rss(query: str, limit: int = 25) -> list[dict[str, str]]:
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    req = urllib.request.Request(url, headers={"User-Agent": "TradingAgentsNewsWeb/1.0"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        body = resp.read()
    root = ET.fromstring(body)
    out: list[dict[str, str]] = []
    for item in root.findall(".//item"):
        if len(out) >= limit:
            break
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        desc = (item.findtext("description") or "").strip()
        out.append(
            {
                "title": title[:500],
                "link": link[:2000],
                "publisher": "Google News (RSS)",
                "summary": desc[:2000],
                "published": pub[:80],
            }
        )
    return out
