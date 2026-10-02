import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://www.mrguider.org/codes/last-beacon-survival-codes/"
STATE_PATH = Path("data/seen_codes.json")
CODE_RE = re.compile(r"^[A-Z0-9][A-Z0-9!_-]{3,24}$")

def load_seen():
    if not STATE_PATH.exists():
        return set()
    return set(json.loads(STATE_PATH.read_text(encoding='utf-8')))

def save_seen(seen):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(sorted(seen), indent=2) + '\n', encoding='utf-8')

def fetch_codes():
    r = requests.get(SOURCE_URL, timeout=30, headers={'User-Agent': 'Renegades-Bot-LB/1.0'})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    candidates = [x.get_text(' ', strip=True) for x in soup.select('code, td')]
    codes = []
    for value in candidates:
        value = value.strip('` ').strip()
        if CODE_RE.fullmatch(value) and value not in codes:
            codes.append(value)
    return codes

def send_discord(code):
    webhook = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook:
        raise RuntimeError('DISCORD_WEBHOOK_URL is missing.')
    payload = {
        'username': 'RENEGADES BOT',
        'content': ('🏴 **RENEGADES BOT**\n━━━━━━━━━━━━━━━━━━━━\n\n'
                    '# 🎁 NEW GIFT CODE\n\n'
                    f'🎁 **{code}**\n\n'
                    '🟢 **Status:** NEW\n\n'
                    '━━━━━━━━━━━━━━━━━━━━\n\n'
                    '⚡ **REDEEM NOW**\n\n'
                    '*Codes can expire without notice.*\n\n'
                    f'🔗 **Source:** [Last Beacon Code Tracker]({SOURCE_URL})\n\n'
                    '🏴 **RENEGADES**'),
        'allowed_mentions': {'parse': []},
    }
    r = requests.post(webhook, json=payload, timeout=30)
    r.raise_for_status()

def main():
    seen = load_seen()
    codes = fetch_codes()
    new_codes = [code for code in codes if code not in seen]
    for code in new_codes:
        send_discord(code)
    seen.update(codes)
    save_seen(seen)
    print(f'Found {len(codes)} codes; sent {len(new_codes)} new codes.')

if __name__ == '__main__':
    main()
