"""Daily update: remove past events, save the time, check links."""
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

IRAN = timezone(timedelta(hours=3, minutes=30))
now = datetime.now(timezone.utc)
today = now.astimezone(IRAN).date().isoformat()

with open("data/events.json", encoding="utf-8") as f:
    data = json.load(f)

# 1. Remove events that already ended (the 9th item is the end date).
removed = 0
for month, cats in data.get("events", {}).items():
    for cat in list(cats.keys()):
        keep = []
        for item in cats[cat]:
            end = item[8] if len(item) > 8 else ""
            if end and end < today:
                removed += 1
            else:
                keep.append(item)
        if keep:
            cats[cat] = keep
        else:
            del cats[cat]

# 2. Save the time of this check.
data["updated"] = now.isoformat(timespec="seconds")
with open("data/events.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

# 3. Collect links from index.html and events.json.
links = set()
try:
    html = open("index.html", encoding="utf-8").read()
    for u in re.findall(r"https?://[^'\"`\s<>\\]+", html):
        u = u.rstrip(",;.")
        if "${" in u or "google.com" in u:
            continue
        links.add(u)
except FileNotFoundError:
    pass
for cats in data.get("events", {}).values():
    for items in cats.values():
        for item in items:
            if len(item) > 7 and str(item[7]).startswith("http"):
                links.add(item[7])


def check(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


lines = ["Link check: " + now.isoformat(timespec="seconds"),
         "404/410 or 0 = probably broken. 403/429 = the site may just block this robot.", ""]
bad = 0
for url in sorted(links):
    code = check(url)
    if not 200 <= code < 400:
        bad += 1
        lines.append(f"{code}  {url}")
if bad == 0:
    lines.append("All links are OK.")
with open("data/link_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Removed {removed} past events. Checked {len(links)} links. Problems: {bad}.")
