#!/usr/bin/env python3
"""Fetch Ayush Shuklai's public GitHub contribution calendar — no token.

GitHub serves the calendar as public HTML at
https://github.com/users/<username>/contributions — the same fragment the
profile page uses. Each day cell is a <td data-date data-level> and its
count lives in the matching <tool-tip> ("N contributions on ...").

BeautifulSoup is used when installed (it is in requirements.txt for the
GitHub Actions workflow); otherwise a stdlib html.parser fallback does
the same job, so the script also runs in minimal environments.

Writes data/contributions.json with the raw days plus derived stats.
Real data only — however sparse the graph is, that is what gets saved.

Usage: python scripts/fetch_contributions.py [username] [out.json]
"""
import json
import re
import sys
from datetime import datetime, timezone

import requests

COUNT_RE = re.compile(r"^(\d[\d,]*) contribution")
NO_RE = re.compile(r"^No contributions")


def parse_days(html):
    days = {}
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        tips = {}
        for tip in soup.find_all("tool-tip"):
            target = tip.get("for")
            if target:
                tips[target] = tip.get_text(strip=True)
        out = {}
        for td in soup.find_all("td"):
            date = td.get("data-date")
            if not date:
                continue
            text = tips.get(td.get("id") or "", "")
            out[date] = {
                "count": _count_from_text(text),
                "level": int(td.get("data-level", 0)),
            }
        return out
    except ImportError:
        pass

    from html.parser import HTMLParser

    class P(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tds = {}
            self.tips = {}
            self._tip_for = None
            self._tip_text = []

        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag == "td" and a.get("data-date"):
                self.tds[a["data-date"]] = {
                    "id": a.get("id"),
                    "level": int(a.get("data-level", 0)),
                }
            elif tag == "tool-tip":
                self._tip_for = a.get("for")
                self._tip_text = []

        def handle_data(self, data):
            if self._tip_for is not None:
                self._tip_text.append(data)

        def handle_endtag(self, tag):
            if tag == "tool-tip" and self._tip_for is not None:
                self.tips[self._tip_for] = "".join(self._tip_text).strip()
                self._tip_for = None

    p = P()
    p.feed(html)
    out = {}
    for date, meta in p.tds.items():
        text = p.tips.get(meta["id"] or "", "")
        out[date] = {"count": _count_from_text(text), "level": meta["level"]}
    return out


def _count_from_text(text):
    if NO_RE.match(text or ""):
        return 0
    m = COUNT_RE.match(text or "")
    return int(m.group(1).replace(",", "")) if m else 0


def derive(days_sorted):
    total = sum(d["count"] for d in days_sorted)
    active = sum(1 for d in days_sorted if d["count"] > 0)
    longest = run = 0
    for d in days_sorted:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for d in reversed(days_sorted):
        if d["count"] > 0:
            current += 1
        else:
            break
    best = max(days_sorted, key=lambda d: d["count"]) if days_sorted else {"date": None, "count": 0}
    monthly = {}
    for d in days_sorted:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    return {
        "total_contributions": total,
        "active_days": active,
        "total_days": len(days_sorted),
        "longest_streak": longest,
        "current_streak": current,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly_totals": monthly,
    }


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else "Ayushshuklai"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "data/contributions.json"
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (profile-readme heatmap refresher)"},
        timeout=30,
    )
    resp.raise_for_status()
    raw = parse_days(resp.text)
    if not raw:
        raise SystemExit(f"No contribution day cells parsed from {url}")
    days = [
        {"date": d, "count": raw[d]["count"], "level": raw[d]["level"]}
        for d in sorted(raw)
    ]
    payload = {
        "username": username,
        "source": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "days": days,
        "derived": derive(days),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    d = payload["derived"]
    print(
        f"{username}: {d['total_days']} days, {d['total_contributions']} contributions, "
        f"{d['active_days']} active days, longest streak {d['longest_streak']} -> {out_path}"
    )


if __name__ == "__main__":
    main()
