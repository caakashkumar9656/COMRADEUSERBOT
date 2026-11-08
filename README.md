# Comrade Userbot

A Telethon userbot for your own Telegram account with 60+ commands and an automatic DM reply.

## Setup
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `API_ID` and `API_HASH` (from https://my.telegram.org).
3. `python userbot.py`. On first run, enter your phone number and the login code.
4. In any chat, send `.help` to see every command.

## Auto DM
- `.autodm on` / `.autodm off`
- `.setdm Your message here`
- Each person gets at most one auto reply per 6 hours, and bots are ignored.
- `.afk <reason>` / `.unafk` works the same way with an AFK message.

## Anti-spam
- `.antispam on` / `.antispam off` - auto-block strangers who flood your DMs
- `.spamlimit 8 10` - block at 8 messages within 10 seconds (default)
- `.allow` / `.disallow` / `.allowed` - whitelist people who should never be blocked
- `.spamlog` - see who was blocked. You also get a note in Saved Messages.
- Your contacts, bots and Telegram itself are never blocked.

Never commit `.env` or `*.session` files. They give full access to your account.
