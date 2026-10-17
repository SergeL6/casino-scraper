import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

URL = "https://www.livescore.com/en-za/online-casinos/"
UA = "casino-bonus-screening-task/1.0"
MODEL = "openai/gpt-oss-120b"
OUTPUT = "data.json"

# alt_key: text found in the table row's image alt
# block_key: name used in the "Features & Information" heading
TARGETS = [
    {"alt_key": "easybet", "block_key": "Easybet Casino", "name": "Easybet",
     "url": "https://easybet.co.za/"},
    {"alt_key": "jackpotcity", "block_key": "Jackpot City Casino", "name": "Jackpot City",
     "url": "https://www.jackpotcity.co.za/"},
    {"alt_key": "tictacbet", "block_key": "Tic Tac Casino", "name": "Tic Tac",
     "url": "https://tictac-bets.co.za/"},
]

client = Groq(api_key=os.getenv("GROQ_API_KEY_1"))

PROMPT = """Extract fields for one online casino from the text below.
Return ONLY a JSON object with exactly these keys:
- "casino": clean casino name, e.g. "Jackpot City"
- "welcome_bonus": the welcome bonus as written, e.g. "100% up to R5000 + 50 Free Spins"
- "wagering_multiplier": number (e.g. 35), or null if not stated in the text
- "min_deposit": string with currency, e.g. "R5", or null if not stated in the text
Use only information in the text. Never guess.

BONUS TEXT: {bonus}
FEATURES TEXT: {features}
RAW NAME: {name}
"""


def robots_ok(url):
    p = urlparse(url)
    rp = RobotFileParser(f"{p.scheme}://{p.netloc}/robots.txt")
    rp.read()
    return rp.can_fetch(UA, url)


def llm_json(prompt):
    for attempt in range(4):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            print(f"  LLM error: {e}")
            if attempt == 3 or "per day" in str(e).lower() or "model_not_found" in str(e):
                raise
            wait = 2 ** (attempt + 1)
            print(f"  retry in {wait}s")
            time.sleep(wait)

def validate(d):
    keys = {"casino", "welcome_bonus", "wagering_multiplier", "min_deposit"}
    if set(d) != keys:
        raise ValueError(f"bad keys: {d}")
    w = d["wagering_multiplier"]
    if w is not None and not isinstance(w, (int, float)):
        raise ValueError(f"wagering not a number: {w}")
    return d


def main():
    if not robots_ok(URL):
        raise SystemExit("robots.txt disallows this page. Switch source.")

    r = requests.get(URL, headers={"User-Agent": UA}, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    page_text = soup.get_text(" ", strip=True)

    rows = {}
    for row in soup.select('[data-id^="br-itm_"]'):
        img = row.select_one('[data-testid="brand-image"]')
        bonus = row.select_one('[data-testid="brand-bonus"]')
        if img and bonus:
            key = img.get("alt", "").lower().replace(" ", "").replace("-", "")
            rows[key] = bonus.get_text(" ", strip=True)

    results = []
    for t in TARGETS:
        bonus_text = next((v for k, v in rows.items() if t["alt_key"] in k), None)
        if not bonus_text:
            print(f"Row not found for {t['alt_key']}, skipping")
            continue

        m = re.search(
            re.escape(t["block_key"])
            + r"[^:]{0,5}: Features & Information(.*?)Withdrawal Speed",
            page_text,
        )
        features = m.group(1) if m else ""

        data = validate(llm_json(PROMPT.format(
            name=t["name"], bonus=bonus_text, features=features)))
        data["casino"] = t["name"]
        data["source_url"] = URL
        data["casino_url"] = t["url"]
        results.append(data)
        print("OK:", data)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(
            {"scraped_at": datetime.now(timezone.utc).isoformat(), "casinos": results},
            f, indent=2, ensure_ascii=False,
        )
    print(f"Wrote {len(results)} casinos to {OUTPUT}")


if __name__ == "__main__":
    main()