"""Comrade Userbot - a Telethon userbot for your own Telegram account.
Prefix: "." (change with PREFIX in .env). Type .help to list commands.
"""
import ast
import asyncio
import base64
import codecs
import json
import operator
import os
import random
import time
from datetime import datetime

from dotenv import load_dotenv
from telethon import TelegramClient, events

load_dotenv()
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
PREFIX = os.environ.get("PREFIX", ".")
SESSION = os.environ.get("SESSION_NAME", "comrade")
STATE_FILE = "state.json"
START = time.time()
DM_COOLDOWN = 6 * 3600  # one auto reply per person per 6 hours

client = TelegramClient(SESSION, API_ID, API_HASH)

# ---------------------------------------------------------------- state
DEFAULT_STATE = {
    "dm_enabled": False,
    "dm_text": "Hi! I'm away from my keyboard right now. I'll reply as soon as I can.",
    "afk": False,
    "afk_reason": "",
    "afk_since": 0,
    "replied": {},
    "antispam": False,
    "spam_limit": 8,
    "spam_window": 10,
    "whitelist": [],
    "spam_log": [],
}


def load_state():
    try:
        with open(STATE_FILE) as f:
            return {**DEFAULT_STATE, **json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_STATE)


def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


state = load_state()

# ---------------------------------------------------------------- registry
COMMANDS = {}


def command(*names):
    def deco(fn):
        for n in names:
            COMMANDS[n] = fn
        fn.names = names
        return fn
    return deco


@client.on(events.NewMessage(outgoing=True))
async def dispatcher(event):
    text = event.raw_text or ""
    if not text.startswith(PREFIX):
        return
    head, _, args = text[len(PREFIX):].partition(" ")
    fn = COMMANDS.get(head.lower())
    if not fn:
        return
    try:
        await fn(event, args.strip())
    except Exception as e:  # keep the bot alive on errors
        await event.edit(f"Error in .{head}: `{type(e).__name__}: {e}`")


async def target_user(event, args):
    """User from reply, else from first arg (username/id)."""
    if event.is_reply:
        return (await event.get_reply_message()).sender_id
    if args:
        return await client.get_entity(args.split()[0])
    return None


def fmt_dur(sec):
    sec = int(sec)
    d, r = divmod(sec, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    return f"{d}d {h}h {m}m {s}s"


# ---------------------------------------------------------------- general
@command("alive")
async def alive(e, a):
    """Check the bot is running"""
    await e.edit(f"**Comrade Userbot is alive**\nUptime: {fmt_dur(time.time() - START)}")


@command("ping")
async def ping(e, a):
    """Latency"""
    t = time.perf_counter()
    await e.edit("Pong...")
    await e.edit(f"Pong! `{(time.perf_counter() - t) * 1000:.0f} ms`")


@command("help")
async def help_(e, a):
    """List commands"""
    seen, lines = set(), []
    for fn in COMMANDS.values():
        if fn in seen:
            continue
        seen.add(fn)
        lines.append(f"`{PREFIX}{fn.names[0]}` - {fn.__doc__ or ''}")
    await e.edit(f"**{len(seen)} commands**\n" + "\n".join(lines))


@command("uptime")
async def uptime(e, a):
    """Bot uptime"""
    await e.edit(f"Up for {fmt_dur(time.time() - START)}")


@command("id")
async def id_(e, a):
    """IDs of chat / replied user"""
    out = f"Chat ID: `{e.chat_id}`"
    if e.is_reply:
        r = await e.get_reply_message()
        out += f"\nUser ID: `{r.sender_id}`\nMessage ID: `{r.id}`"
    await e.edit(out)


@command("info")
async def info(e, a):
    """Info about replied user or @username"""
    u = await target_user(e, a)
    if u is None:
        u = await client.get_me()
    elif isinstance(u, int):
        u = await client.get_entity(u)
    await e.edit(
        f"**Name:** {u.first_name or ''} {u.last_name or ''}\n"
        f"**Username:** @{u.username}\n**ID:** `{u.id}`\n"
        f"**Bot:** {u.bot}\n**Premium:** {getattr(u, 'premium', False)}"
    )


@command("chatinfo")
async def chatinfo(e, a):
    """Info about this chat"""
    c = await e.get_chat()
    title = getattr(c, "title", None) or getattr(c, "first_name", "")
    await e.edit(f"**Title:** {title}\n**ID:** `{c.id}`\n**Type:** {type(c).__name__}")


@command("echo")
async def echo(e, a):
    """Repeat text"""
    await e.edit(a or "Nothing to echo")


@command("repeat")
async def repeat(e, a):
    """.repeat <n> <text> (max 10)"""
    n, _, t = a.partition(" ")
    await e.delete()
    for _ in range(min(int(n), 10)):
        await client.send_message(e.chat_id, t)
        await asyncio.sleep(0.7)


# ---------------------------------------------------------------- text tools
async def text_of(e, a):
    if a:
        return a
    if e.is_reply:
        return (await e.get_reply_message()).raw_text or ""
    return ""


@command("upper")
async def upper(e, a):
    """UPPERCASE"""
    await e.edit((await text_of(e, a)).upper())


@command("lower")
async def lower(e, a):
    """lowercase"""
    await e.edit((await text_of(e, a)).lower())


@command("title")
async def title(e, a):
    """Title Case"""
    await e.edit((await text_of(e, a)).title())


@command("reverse")
async def reverse(e, a):
    """Reverse text"""
    await e.edit((await text_of(e, a))[::-1])


@command("mock")
async def mock(e, a):
    """sPoNgEbOb text"""
    t = await text_of(e, a)
    await e.edit("".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(t)))


@command("bold")
async def bold(e, a):
    """Bold text"""
    await e.edit(f"**{await text_of(e, a)}**")


@command("italic")
async def italic(e, a):
    """Italic text"""
    await e.edit(f"__{await text_of(e, a)}__")


@command("mono")
async def mono(e, a):
    """Monospace text"""
    await e.edit(f"`{await text_of(e, a)}`")


@command("strike")
async def strike(e, a):
    """Strikethrough text"""
    await e.edit(f"~~{await text_of(e, a)}~~")


@command("spoiler")
async def spoiler(e, a):
    """Spoiler text"""
    await e.edit(f"||{await text_of(e, a)}||")


@command("count")
async def count(e, a):
    """Count chars/words"""
    t = await text_of(e, a)
    await e.edit(f"Characters: {len(t)}\nWords: {len(t.split())}")


# ---------------------------------------------------------------- fun
async def emoji_game(e, emoji):
    await e.delete()
    await client.send_file(e.chat_id, __import__("telethon").types.InputMediaDice(emoji))


@command("dice")
async def dice(e, a):
    """Send a dice"""
    await emoji_game(e, "🎲")


@command("dart")
async def dart(e, a):
    """Throw a dart"""
    await emoji_game(e, "🎯")


@command("basket")
async def basket(e, a):
    """Basketball"""
    await emoji_game(e, "🏀")


@command("football")
async def football(e, a):
    """Football"""
    await emoji_game(e, "⚽")


@command("slot")
async def slot(e, a):
    """Slot machine"""
    await emoji_game(e, "🎰")


@command("bowl")
async def bowl(e, a):
    """Bowling"""
    await emoji_game(e, "🎳")


@command("coin")
async def coin(e, a):
    """Flip a coin"""
    await e.edit(random.choice(["Heads", "Tails"]))


@command("roll")
async def roll(e, a):
    """.roll [max] random number"""
    await e.edit(f"{random.randint(1, int(a) if a else 100)}")


@command("choose")
async def choose(e, a):
    """.choose a | b | c"""
    await e.edit(random.choice([x.strip() for x in a.split("|")]))


@command("eightball", "8ball")
async def eightball(e, a):
    """Magic 8-ball"""
    await e.edit(random.choice(["Yes", "No", "Maybe", "Definitely", "Ask again later", "Doubtful"]))


@command("slap")
async def slap(e, a):
    """Slap with a trout"""
    await e.edit(f"slaps {a or 'someone'} with a large trout")


@command("hug")
async def hug(e, a):
    """Hug someone"""
    await e.edit(f"hugs {a or 'everyone'}")


@command("hack")
async def hack(e, a):
    """.hack [name] - fake hacking prank with progress bar"""
    target = a
    if not target and e.is_reply:
        r = await e.get_reply_message()
        s = await r.get_sender()
        target = (s.first_name or "target") if s else "target"
    target = target or "target"
    steps = [(5, "Connecting to server"), (15, "Bypassing firewall"), (30, "Locating target"),
             (50, "Accessing chats"), (70, "Downloading data"), (90, "Erasing traces"),
             (100, "Hack complete")]
    for pct, msg in steps:
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        await e.edit(f"💻 **Hacking {target}**\n`{bar}` {pct}%\n{msg}...")
        await asyncio.sleep(1.2)
    await e.edit(f"😂 **{target}, you have been pranked!**\nNothing was hacked. It's just a joke 😄")


# ---------------------------------------------------------------- utilities
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.USub: operator.neg}


def safe_eval(node):
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](safe_eval(node.left), safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](safe_eval(node.operand))
    raise ValueError("unsupported expression")


@command("calc")
async def calc(e, a):
    """Calculator, e.g. .calc 2*(3+4)"""
    await e.edit(f"`{a}` = `{safe_eval(ast.parse(a, mode='eval'))}`")


@command("time")
async def time_(e, a):
    """Current time"""
    await e.edit(datetime.now().strftime("%H:%M:%S"))


@command("date")
async def date(e, a):
    """Current date"""
    await e.edit(datetime.now().strftime("%A, %d %B %Y"))


@command("b64e")
async def b64e(e, a):
    """Base64 encode"""
    await e.edit(f"`{base64.b64encode((await text_of(e, a)).encode()).decode()}`")


@command("b64d")
async def b64d(e, a):
    """Base64 decode"""
    await e.edit(base64.b64decode(await text_of(e, a)).decode())


@command("hex")
async def hex_(e, a):
    """Text to hex"""
    await e.edit(f"`{(await text_of(e, a)).encode().hex()}`")


@command("bin")
async def bin_(e, a):
    """Text to binary"""
    await e.edit("`" + " ".join(f"{b:08b}" for b in (await text_of(e, a)).encode()) + "`")


@command("rot13")
async def rot13(e, a):
    """ROT13 text"""
    await e.edit(codecs.encode(await text_of(e, a), "rot_13"))


# ---------------------------------------------------------------- moderation / messages
@command("del")
async def del_(e, a):
    """Delete replied message (and this one)"""
    if e.is_reply:
        await (await e.get_reply_message()).delete()
    await e.delete()


@command("purge")
async def purge(e, a):
    """Reply to a message: delete everything from it to now"""
    if not e.is_reply:
        return await e.edit("Reply to the first message to purge.")
    rid = (await e.get_reply_message()).id
    ids = [m.id async for m in client.iter_messages(e.chat_id, min_id=rid - 1)]
    await client.delete_messages(e.chat_id, ids)


@command("pin")
async def pin(e, a):
    """Pin replied message"""
    await client.pin_message(e.chat_id, (await e.get_reply_message()).id)
    await e.edit("Pinned.")


@command("unpin")
async def unpin(e, a):
    """Unpin replied message (or all)"""
    r = await e.get_reply_message() if e.is_reply else None
    await client.unpin_message(e.chat_id, r.id if r else None)
    await e.edit("Unpinned.")


@command("ban")
async def ban(e, a):
    """Ban user (reply / @user)"""
    u = await target_user(e, a)
    await client.edit_permissions(e.chat_id, u, view_messages=False)
    await e.edit("Banned.")


@command("unban")
async def unban(e, a):
    """Unban user"""
    u = await target_user(e, a)
    await client.edit_permissions(e.chat_id, u, view_messages=True)
    await e.edit("Unbanned.")


@command("kick")
async def kick(e, a):
    """Kick user"""
    u = await target_user(e, a)
    await client.kick_participant(e.chat_id, u)
    await e.edit("Kicked.")


@command("mute")
async def mute(e, a):
    """Mute user in group"""
    u = await target_user(e, a)
    await client.edit_permissions(e.chat_id, u, send_messages=False)
    await e.edit("Muted.")


@command("unmute")
async def unmute(e, a):
    """Unmute user"""
    u = await target_user(e, a)
    await client.edit_permissions(e.chat_id, u, send_messages=True)
    await e.edit("Unmuted.")


@command("save")
async def save(e, a):
    """Save replied message to Saved Messages"""
    await client.forward_messages("me", await e.get_reply_message())
    await e.edit("Saved.")


@command("fwd")
async def fwd(e, a):
    """.fwd <chat> forward replied message"""
    await client.forward_messages(a, await e.get_reply_message())
    await e.edit("Forwarded.")


@command("copy")
async def copy(e, a):
    """Re-send replied message without forward tag"""
    r = await e.get_reply_message()
    await e.delete()
    await client.send_message(e.chat_id, r.text, file=r.media)


@command("block")
async def block(e, a):
    """Block user"""
    u = await target_user(e, a)
    from telethon.tl.functions.contacts import BlockRequest
    await client(BlockRequest(u))
    await e.edit("Blocked.")


@command("unblock")
async def unblock(e, a):
    """Unblock user"""
    u = await target_user(e, a)
    from telethon.tl.functions.contacts import UnblockRequest
    await client(UnblockRequest(u))
    await e.edit("Unblocked.")


@command("members")
async def members(e, a):
    """Member count of this chat"""
    await e.edit(f"Members: {(await client.get_participants(e.chat_id, limit=0)).total}")


@command("typing")
async def typing(e, a):
    """.typing <sec> show typing status"""
    await e.delete()
    async with client.action(e.chat_id, "typing"):
        await asyncio.sleep(min(int(a or 5), 60))


@command("setbio")
async def setbio(e, a):
    """Change your bio"""
    from telethon.tl.functions.account import UpdateProfileRequest
    await client(UpdateProfileRequest(about=a))
    await e.edit("Bio updated.")


@command("setname")
async def setname(e, a):
    """Change first name"""
    from telethon.tl.functions.account import UpdateProfileRequest
    await client(UpdateProfileRequest(first_name=a))
    await e.edit("Name updated.")


# ---------------------------------------------------------------- AFK + auto DM
@command("afk")
async def afk(e, a):
    """Go AFK with optional reason"""
    state.update(afk=True, afk_reason=a, afk_since=time.time())
    state["replied"] = {}
    save_state()
    await e.edit(f"AFK mode on. {a}")


@command("unafk")
async def unafk(e, a):
    """Turn AFK off"""
    state["afk"] = False
    save_state()
    await e.edit("Welcome back!")


@command("autodm")
async def autodm(e, a):
    """.autodm on|off - automatic reply to new DMs"""
    state["dm_enabled"] = a.lower() == "on"
    save_state()
    await e.edit(f"Auto DM reply: {'ON' if state['dm_enabled'] else 'OFF'}")


@command("setdm")
async def setdm(e, a):
    """.setdm <text> set the auto DM message"""
    state["dm_text"] = a
    save_state()
    await e.edit("Auto DM message saved.")


@command("dmstatus")
async def dmstatus(e, a):
    """Show auto DM settings"""
    await e.edit(f"Auto DM: {'ON' if state['dm_enabled'] else 'OFF'}\nMessage: {state['dm_text']}\n"
                 f"AFK: {state['afk']}")


@command("dmreset")
async def dmreset(e, a):
    """Reset the once-per-person auto reply memory"""
    state["replied"] = {}
    save_state()
    await e.edit("Auto reply memory cleared.")


# ---------------------------------------------------------------- anti-spam
recent = {}  # user_id -> timestamps of recent messages


async def uid_of(e, a):
    u = await target_user(e, a)
    if u is None:
        return e.chat_id if e.is_private else None
    return u if isinstance(u, int) else u.id


@command("antispam")
async def antispam(e, a):
    """.antispam on|off - auto-block DM spammers"""
    state["antispam"] = a.lower() == "on"
    save_state()
    await e.edit(f"Anti-spam: {'ON' if state['antispam'] else 'OFF'} "
                 f"(block at {state['spam_limit']} messages in {state['spam_window']}s)")


@command("spamlimit")
async def spamlimit(e, a):
    """.spamlimit <messages> <seconds> e.g. .spamlimit 8 10"""
    n, s = a.split()
    state["spam_limit"], state["spam_window"] = max(2, int(n)), max(2, int(s))
    save_state()
    await e.edit(f"Block at {state['spam_limit']} messages in {state['spam_window']}s.")


@command("allow")
async def allow(e, a):
    """Whitelist a user from anti-spam (reply / @user / in their DM)"""
    uid = await uid_of(e, a)
    if uid is None:
        return await e.edit("Reply to someone or use it in their DM.")
    if uid not in state["whitelist"]:
        state["whitelist"].append(uid)
        save_state()
    await e.edit(f"Whitelisted `{uid}`.")


@command("disallow")
async def disallow(e, a):
    """Remove a user from the whitelist"""
    uid = await uid_of(e, a)
    if uid in state["whitelist"]:
        state["whitelist"].remove(uid)
        save_state()
    await e.edit(f"Removed `{uid}` from whitelist.")


@command("allowed")
async def allowed(e, a):
    """Show whitelisted user IDs"""
    await e.edit("Whitelist: " + (", ".join(f"`{i}`" for i in state["whitelist"]) or "empty"))


@command("spamlog")
async def spamlog(e, a):
    """Show recently auto-blocked spammers"""
    log = state["spam_log"][-10:]
    await e.edit("**Blocked spammers**\n" + ("\n".join(log) or "None yet"))


@client.on(events.NewMessage(incoming=True, func=lambda ev: ev.is_private))
async def spam_guard(event):
    if not state["antispam"]:
        return
    sender = await event.get_sender()
    if (sender is None or sender.bot or sender.id == 777000
            or sender.id in state["whitelist"]
            or getattr(sender, "contact", False)
            or getattr(sender, "mutual_contact", False)):
        return  # contacts, bots, Telegram and whitelisted users are never blocked
    now = time.time()
    hits = [t for t in recent.get(sender.id, []) if now - t < state["spam_window"]]
    hits.append(now)
    recent[sender.id] = hits
    if len(hits) < state["spam_limit"]:
        return
    from telethon.tl.functions.contacts import BlockRequest
    await client(BlockRequest(sender.id))
    recent.pop(sender.id, None)
    who = f"{sender.first_name or ''} (@{sender.username}) `{sender.id}`"
    state["spam_log"] = (state["spam_log"] + [f"{datetime.now():%d %b %H:%M} - {who}"])[-50:]
    save_state()
    await client.send_message("me", f"Anti-spam blocked {who} for sending "
                                    f"{len(hits)} messages in {state['spam_window']}s.")


@client.on(events.NewMessage(incoming=True, func=lambda ev: ev.is_private))
async def auto_reply(event):
    if not (state["dm_enabled"] or state["afk"]):
        return
    sender = await event.get_sender()
    if sender is None or sender.bot or getattr(sender, "is_self", False):
        return
    uid = str(sender.id)
    if time.time() - state["replied"].get(uid, 0) < DM_COOLDOWN:
        return  # already replied recently; avoids spamming people
    if state["afk"]:
        text = f"I'm AFK since {fmt_dur(time.time() - state['afk_since'])}. {state['afk_reason']}"
    else:
        text = state["dm_text"]
    await event.reply(text)
    state["replied"][uid] = time.time()
    save_state()


async def main():
    await client.start()  # asks for phone number + login code on first run
    print(f"Userbot running with {len(set(COMMANDS.values()))} commands. Prefix: {PREFIX}")
    await client.run_until_disconnected()


if __name__ == "__main__":
    client.loop.run_until_complete(main())
