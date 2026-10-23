"""
Configuration settings for Telegram File Streamer.
Reads configuration from environment variables or .env file.
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram API Credentials
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")

    # Telegram Bot Token
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # Telegram Storage Channel ID (e.g. -1001234567890)
    _raw_bin = os.getenv("BIN_CHANNEL", "0").strip()
    BIN_CHANNEL: int = int(_raw_bin) if _raw_bin and _raw_bin != "0" else 0

    # Public Base URL of your deployed application
    # Automatically falls back to Render's RENDER_EXTERNAL_URL if deployed on Render
    _raw_base = os.getenv("BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "http://localhost:8000"
    BASE_URL: str = _raw_base.rstrip("/")

    # Server binding
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))

    # Optional: Authorized Telegram User IDs
    _AUTH_USERS_RAW: str = os.getenv("AUTH_USERS", "")
    AUTH_USERS: List[int] = [
        int(uid.strip())
        for uid in _AUTH_USERS_RAW.split(",")
        if uid.strip().isdigit()
    ]

    # Optional: Telegram User Session String (Telegram Premium for 10x-50x download speeds)
    SESSION_STRING: str = os.getenv("SESSION_STRING", "").strip()

    # Secret key used for optional link signing
    SECRET_KEY: str = os.getenv("SECRET_KEY", "telegram-file-streamer-secret-key")

    # MTProto download chunk size (in bytes, max 1024 * 1024 = 1MB)
    CHUNK_SIZE: int = 1024 * 1024

    # Keep-alive ping interval in seconds
    PING_INTERVAL_SECONDS: int = int(os.getenv("PING_INTERVAL_SECONDS", "300"))
