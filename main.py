import json
import time
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

# === Flask ===
app = Flask("")


@app.route("/")
def home():
    return "Bot is running!"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


# === Config ===
api_id = 2841031
api_hash = 'f855909578d967fcb258e1b813ade3d0'
session_string = '1BVtsOKYBu08tWbn-xJaTMh6WJdI5es7fE0-zov7U2_LbviDKToqDeL2eKgA5hEVInCn6rpPUGP-FDRYiWHQnynKWvNG37BaVbX06YsspTO0qwvvhqlxoUSgOiEJLsG1kUYjBukDQTHHBakqvB0mTryW9knemVcvWorTerFd7OjAeokEhbJLnKOXSrra8bB9wY2alLg2XY5phHIsY-Pbc13mRgOBnXklqnL0AFtvfAMtxDIxnNLi6OSuTLh5NHLJGp_480S4sT5qBWH8tRdkfiddPhzxPVHd0Ib9YQcbL_i2tBtW3Q_qm4jrb7Uz50ILIqXO7HgS2-dpB7Rts9dy07kQP8trBQEc='

client = TelegramClient(StringSession(session_string), api_id, api_hash)

# === State ===
start_time = time.time()
is_afk = False
afk_reason = ""
afk_time = None
OWNER_ID = None
FILTERS_FILE = "filters.json"

# === Load filters from file ===
try:
    with open(FILTERS_FILE, "r") as f:
        filters = json.load(f)
except FileNotFoundError:
    filters = {}


def save_filters():
    with open(FILTERS_FILE, "w") as f:
        json.dump(filters, f, indent=2)


# === AFK ===
@client.on(events.NewMessage(pattern=r'\.afk(?: (.*))?', outgoing=True))
async def afk_handler(event):
    global is_afk, afk_reason, afk_time
    if event.sender_id != OWNER_ID:
        return
    afk_reason = event.pattern_match.group(1) or "Tidak ada alasan."
    afk_time = datetime.now()
    is_afk = True
    await event.edit(f"✅ Sekarang kamu AFK: {afk_reason}")


@client.on(events.NewMessage(outgoing=True))
async def disable_afk(event):
    global is_afk, afk_reason, afk_time
    if event.sender_id != OWNER_ID or not is_afk:
        return
    if event.raw_text.startswith(".afk"):
        return
    is_afk = False
    delta = datetime.now() - afk_time if afk_time else None
    durasi = f"{delta.seconds//3600}h {(delta.seconds//60)%60}m {delta.seconds%60}s" if delta else "?"
    await event.reply(f"Tidak AFK lagi. (AFK selama {durasi})")
    afk_reason = ""
    afk_time = None


@client.on(events.NewMessage())
async def afk_responder(event):
    if not is_afk or event.sender_id == OWNER_ID:
        return

    if event.is_private:
        pass
    elif event.is_group or event.is_channel:
        if not event.mentioned:
            if event.is_reply:
                reply_msg = await event.get_reply_message()
                if reply_msg.sender_id != OWNER_ID:
                    return
            else:
                return

    delta = datetime.now() - afk_time if afk_time else None
    durasi = f"{delta.seconds//3600}h {(delta.seconds//60)%60}m {delta.seconds%60}s" if delta else "?"

    await event.reply(f"Saya sedang AFK.\n"
                      f"⏱️ Sejak: {durasi}\n"
                      f"📝 Alasan: {afk_reason}")


# === Filter ===
@client.on(events.NewMessage(pattern=r"\.filter (\S+) (.+)", outgoing=True))
async def add_filter(event):
    if event.sender_id != OWNER_ID:
        return
    keyword = event.pattern_match.group(1).lower()
    response = event.pattern_match.group(2)
    filters[keyword] = response
    save_filters()
    await event.reply(f"✅ Filter ditambahkan:\n`{keyword}` → `{response}`")


@client.on(events.NewMessage(pattern=r"\.stop (\S+)", outgoing=True))
async def remove_filter(event):
    if event.sender_id != OWNER_ID:
        return
    keyword = event.pattern_match.group(1).lower()
    if keyword in filters:
        del filters[keyword]
        save_filters()
        await event.reply(f"🗑️ Filter `{keyword}` telah dihapus.")
    else:
        await event.reply(f"⚠️ Filter `{keyword}` tidak ditemukan.")


@client.on(events.NewMessage(pattern=r"\.filters", outgoing=True))
async def list_filters(event):
    if event.sender_id != OWNER_ID:
        return
    if not filters:
        await event.reply("⚠️ Belum ada filter yang disimpan.")
        return
    msg = "**📄 Daftar Filter Tersimpan:**\n\n"
    for keyword, response in filters.items():
        msg += f"🔹 `{keyword}` → `{response}`\n"
    await event.reply(msg)


@client.on(events.NewMessage())
async def filter_watcher(event):
    if event.sender_id == OWNER_ID:
        return
    text = event.raw_text.lower()
    for keyword, response in filters.items():
        if keyword in text:
            await event.reply(response)
            break


# === Start ===
async def main():
    global OWNER_ID
    await client.start()
    me = await client.get_me()
    OWNER_ID = me.id
    print("Bot aktif sebagai", me.username or me.first_name)
    await client.run_until_disconnected()


from keep_alive import keep_alive

keep_alive()
client.loop.run_until_complete(main())
