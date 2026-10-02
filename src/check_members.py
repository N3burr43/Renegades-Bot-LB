import json
import os
from pathlib import Path

import requests

API = 'https://discord.com/api/v10'
CHANNEL_ID = '1555677241340330166'
STATE_PATH = Path('data/seen_members.json')

def headers():
    token = os.environ.get('DISCORD_BOT_TOKEN')
    if not token:
        raise RuntimeError('DISCORD_BOT_TOKEN is missing.')
    return {'Authorization': f'Bot {token}', 'Content-Type': 'application/json'}

def get_json(path, params=None):
    r = requests.get(API + path, headers=headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def find_guild():
    guilds = get_json('/users/@me/guilds')
    for guild in guilds:
        channels = get_json(f"/guilds/{guild['id']}/channels")
        if any(str(c['id']) == CHANNEL_ID for c in channels):
            return guild
    raise RuntimeError(f'Could not find a guild containing channel {CHANNEL_ID}.')

def get_members(guild_id):
    members = []
    after = '0'
    while True:
        batch = get_json(f'/guilds/{guild_id}/members', {'limit': 1000, 'after': after})
        members.extend(batch)
        if len(batch) < 1000:
            break
        after = batch[-1]['user']['id']
    return members

def load_seen():
    if not STATE_PATH.exists():
        return None
    return set(json.loads(STATE_PATH.read_text(encoding='utf-8')))

def save_seen(seen):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(sorted(seen), indent=2) + '\n', encoding='utf-8')

def send_welcome(member):
    user = member['user']
    name = member.get('nick') or user.get('global_name') or user.get('username') or 'New member'
    payload = {
        'content': (
            '🏴 **RENEGADES**\n'
            '━━━━━━━━━━━━━━━━━━━━\n\n'
            '🎉 **NEW MEMBER**\n\n'
            f'👤 **{name}**\n'
            f'🔗 <@{user["id"]}>\n\n'
            '🔥 **Welcome to RENEGADES!**\n\n'
            '━━━━━━━━━━━━━━━━━━━━\n'
            '🏴 *Enjoy the server and good luck in Last Beacon!*'
        ),
        'allowed_mentions': {'parse': []},
    }
    r = requests.post(f'{API}/channels/{CHANNEL_ID}/messages', headers=headers(), json=payload, timeout=30)
    r.raise_for_status()

def main():
    guild = find_guild()
    members = get_members(guild['id'])
    current = {m['user']['id'] for m in members}
    seen = load_seen()

    if seen is None:
        save_seen(current)
        print(f'Initialized member state for {len(current)} members; no welcome messages sent.')
        return

    new_members = [m for m in members if m['user']['id'] not in seen]
    for member in new_members:
        send_welcome(member)

    save_seen(current)
    print(f'Checked {len(current)} members; welcomed {len(new_members)} new members.')

if __name__ == '__main__':
    main()
