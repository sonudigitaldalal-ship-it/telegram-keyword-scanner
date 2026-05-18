import asyncio
from telethon import TelegramClient

API_ID = 28181640
API_HASH = "883ff23b07b75a58c39052bd62e8810b"
PHONE = "+919818719623"
PASSWORD = "ksharma80"

async def login():
    client = TelegramClient("keyword_scanner_bot", API_ID, API_HASH)
    await client.start(phone=PHONE, password=PASSWORD)
    print("✅ Login successful! Session saved.")
    await client.disconnect()

asyncio.run(login())
