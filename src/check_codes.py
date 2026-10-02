import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SOURCES = [
    ('UCNGame', 'https://ucngame.com/codes/last-beacon-codes/'),
    ('MrGuider', 'https://www.mrguider.org/codes/last-beacon-survival-codes/'),
]
STATE_PATH = Path('data/seen_codes.json')
CODE_RE = re.compile(r'^[A-Z0-9][A-Z0-9!_-]{3,24}$')

def load_seen():
    if not STATE_PATH.exists():
        return set()
    return set(json.loads(STATE_PATH.read_text(encoding='utf-8')))

def save_seen(seen):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(sorted(seen), indent=2) + '\n', encoding='utf-8')

def fetch_codes():
    found = {}
    for name, url in SOURCES:
        try:
            r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0 (compatible; Renegades-Bot-LB/1.0)'})
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            for el in soup.select('code, td'):
                value = el.get_text(' ', strip=True).strip('` ').strip()
                if CODE_RE.fullmatch(value):
                    found.setdefault(value, (name, url))
        except requests.RequestException as exc:
            print(f'Source unavailable: {url} ({exc})')
    return found

def send_discord(code, name, url):
    webhook = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook:
        raise RuntimeError('DISCORD_WEBHOOK_URL is missing.')
    payload = {
        'username': 'RENEGADES BOT',
        'content': f'🏴 **RENEGADES BOT**\n━━━━━━━━━━━━━━━━━━━━\n\n# 🎁 NEW GIFT CODE\n\n🎁 **{code}**\n\n🟢 **Status:** NEW\n\n━━━━━━━━━━━━━━━━━━━━\n\n⚡ **REDEEM NOW**\n\n*Codes can expire without notice.*\n\n🔗 **Source:** [{name}]({url})\n\n🏴 **RENEGADES**',
        'allowed_mentions': {'parse': []},
    }
    r = requests.post(webhook, json=payload, timeout=30)
    r.raise_for_status()

def main():
    seen = load_seen()
    codes = fetch_codes()
    new_codes = [c for c in codes if c not in seen]
    for code in new_codes:
        name, url = codes[code]
        send_discord(code, name, url)
    seen.update(codes.keys())
    save_seen(seen)
    print(f'Found {len(codes)} codes; sent {len(new_codes)} new codes.')

if __name__ == '__main__':
    main()
