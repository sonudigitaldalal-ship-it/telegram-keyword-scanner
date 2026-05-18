import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterEmpty
import os

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
PASSWORD = os.getenv("PASSWORD")
OTP = os.getenv("OTP", "")
MAX_RESULTS = 5

PLAN_A_CHANNELS = [
    ("Trending Loot Deals", "https://telegram.me/+CmTgiyYxFC0zMjg1"),
    ("Deals Point", "https://telegram.me/+KgUrCwnDny02ZDk1"),
    ("FRCP", "https://telegram.me/+LNRQ0Y1-9RkzZDRl"),
    ("Alibaba 2.0", "https://t.me/+AdUPh392S6xhNmY1"),
]
PLAN_B_CHANNELS = PLAN_A_CHANNELS + [
    ("OMG Loot Deals", "https://telegram.me/+U0JGtNSiohCClvnC"),
    ("Offerbox", "https://telegram.me/+Th6aG5Zaxz_i_u7a"),
    ("Lallantop Deals", "https://telegram.me/+QtY0L4n6LP01SN2v"),
]
PLAN_C_CHANNELS = PLAN_B_CHANNELS + [
    ("Rapid Deals", "rapiddeals_unlimited"),
    ("DV Deals", "https://telegram.me/+-o6XWyLrbTMxMTI1"),
]
PLANS = {
    "a": {"name": "Plan A", "channels": PLAN_A_CHANNELS},
    "b": {"name": "Plan B", "channels": PLAN_B_CHANNELS},
    "c": {"name": "Plan C", "channels": PLAN_C_CHANNELS},
}

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def search_channel(client, display_name, channel_id, keyword):
    results = []
    try:
        entity = await client.get_entity(channel_id)
        messages = await client(SearchRequest(peer=entity, q=keyword, filter=InputMessagesFilterEmpty(), limit=MAX_RESULTS))
        channel_username = getattr(entity, "username", None)
        for msg in messages.messages:
            if msg.message:
                post_link = f"https://t.me/{channel_username}/{msg.id}" if channel_username else channel_id
                results.append({
                    "display_name": display_name,
                    "text": msg.message[:300],
                    "date": msg.date.strftime("%d %b %Y, %I:%M %p"),
                    "link": post_link,
                })
    except Exception as exc:
        logger.warning("Could not search '%s': %s", display_name, exc)
    return results

async def search_all_channels(client, channels, keyword):
    tasks = [search_channel(client, name, cid, keyword) for name, cid in channels]
    nested = await asyncio.gather(*tasks)
    return [item for sublist in nested for item in sublist]

def format_result(result, index):
    return f"*{index}. {result['display_name']}*\n🗓 {result['date']}\n📝 {result['text']}\n🔗 [View Post]({result['link']})"

def make_bot(client):
    @client.on(events.NewMessage(pattern=r"^/start"))
    async def handle_start(event):
        await event.respond("👋 *Telegram Keyword Scanner Bot*\n\n/a `<keyword>` — Plan A\n/b `<keyword>` — Plan B\n/c `<keyword>` — Plan C\n/plans — show all plans", parse_mode="md")
    
    @client.on(events.NewMessage(pattern=r"^/help"))
    async def handle_help(event):
        await handle_start(event)
    
    @client.on(events.NewMessage(pattern=r"^/plans"))
    async def handle_plans(event):
        msg = "📋 *All Plans:*\n\n"
        for key, plan in PLANS.items():
            names = ", ".join(name for name, _ in plan["channels"])
            msg += f"*/{key} — {plan['name']}* ({len(plan['channels'])} channels)\n{names}\n\n"
        await event.respond(msg, parse_mode="md")
    
    async def handle_search(event, plan_key):
        parts = event.raw_text.split(maxsplit=1)
        if len(parts) < 2:
            await event.respond(f"⚠️ Please provide a keyword.\nExample: `/{plan_key} iPhone`", parse_mode="md")
            return
        keyword = parts[1].strip()
        plan = PLANS[plan_key]
        channels = plan["channels"]
        status = await event.respond(f"🔍 Searching {len(channels)} channels for `{keyword}` ...", parse_mode="md")
        results = await search_all_channels(client, channels, keyword)
        if not results:
            await status.edit(f"😕 No results found for `{keyword}`", parse_mode="md")
            return
        await status.edit(f"✅ Found {len(results)} result(s):", parse_mode="md")
        for i, result in enumerate(results, 1):
            try:
                await event.respond(format_result(result, i), parse_mode="md")
                await asyncio.sleep(0.3)
            except Exception as exc:
                logger.warning("Could not send result %d: %s", i, exc)
    
    @client.on(events.NewMessage(pattern=r"^/a\b"))
    async def handle_a(event):
        await handle_search(event, "a")
    
    @client.on(events.NewMessage(pattern=r"^/b\b"))
    async def handle_b(event):
        await handle_search(event, "b")
    
    @client.on(events.NewMessage(pattern=r"^/c\b"))
    async def handle_c(event):
        await handle_search(event, "c")

async def main():
    def otp_callback():
        if OTP:
            logger.info("✅ Using OTP from environment variable")
            return OTP
        logger.error("❌ OTP not provided in environment variable")
        raise ValueError("OTP required but not set in OTP environment variable")
    
    client = TelegramClient("keyword_scanner_bot", API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER, password=PASSWORD, code_callback=otp_callback)
    make_bot(client)
    me = await client.get_me()
    logger.info("✅ Bot running as @%s", me.username)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
