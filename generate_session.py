"""
Generate a Pyrogram Session String using your Telegram account (with Telegram Premium).
This enables the server to stream files using unthrottled Telegram Premium speeds!
"""
import asyncio
from pyrogram import Client
from app.config import Config

API_ID = Config.API_ID or 2639390
API_HASH = Config.API_HASH or "a07ce03a85ac6f70ec9ff91fe0b7dfd9"

async def main():
    print("=" * 60)
    print("  Telegram Premium Session String Generator")
    print("=" * 60)
    print("Log in with your Telegram account (phone number + login code).")
    print("This unlocks full Telegram Premium download speeds on your server!\n")

    async with Client("user_gen_session", in_memory=True, api_id=API_ID, api_hash=API_HASH) as app:
        session_string = await app.export_session_string()
        me = await app.get_me()
        print("\n" + "=" * 60)
        print(f"SUCCESS! Logged in as: {me.first_name} (@{me.username})")
        print(f"Telegram Premium Active: {me.is_premium}")
        print("=" * 60)
        print("\nYour SESSION_STRING:\n")
        print(session_string)
        print("\n" + "=" * 60)
        print("Now set this in your Render Environment Variables:")
        print("Key:   SESSION_STRING")
        print("Value: (paste the long string above)")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
