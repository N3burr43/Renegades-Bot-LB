import json
import os
import re
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SOURCES = [('UCNGame', 'https://ucngame.com/codes/last-beacon-codes/')]
STATE_PATH = Path('data/seen_codes.json')
CODE_RE = re.compile(r'^[A-Z0-9][A-Z0-9!_-]{3,24}$')
DATE_RE = re.compile(r'Valid until ([A-Za-z]+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})', re.I)
MONTHS = {m.lower(): i for i, m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'], 1)}

def load_seen():
    if not STATE_PATH.exists():
        return set()
    return set(json.loads(STATE_PATH.read_text(encoding='utf-8')))

def save_seen(seen):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(sorted(seen), indent=2) + '\n', encoding='utf-8')

def expiry_date(text):
    match = DATE_RE.search(text)
    if not match:
        return None
    raw = re.sub(r'(\d)(st|nd|rd|th)', r'\1', match.group(1))
    raw = raw.replace(',', '')
    parts = raw.split()
    if len(parts) != 3:
        return None
    month = MONTHS.get(parts[0].lower())
    if not month:
        return None
    return date(int(parts[2]), month, int(parts[1]))

def fetch_codes():
    found = {}
    for name, url in SOURCES:
        r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0 (compatible; Renegades-Bot-LB/1.0)'})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        for row in soup.select('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue
            code = cells[0].get_text(' ', strip=True).strip('` ').strip()
            details = ' '.join(c.get_text(' ', strip=True) for c in cells[1:])
            if not CODE_RE.fullmatch(code):
                continue
            expires = expiry_date(details)
            if expires is not None and expires < date.today():
                print(f'Skipping expired code: {code} (expired {expires})')
                continue
            found.setdefault(code, (name, url))
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
    print(f'Found {len(codes)} active codes; sent {len(new_codes)} new codes.')

if __name__ == '__main__':
    main()
