"""
Utility helper functions for Telegram File Streamer.
"""

import hmac
import hashlib
import mimetypes
import re
from typing import Optional, Tuple, Dict, Any
from pyrogram.types import Message
from app.config import Config


def human_readable_size(size_bytes: int) -> str:
    """Convert bytes into human-readable format (B, KB, MB, GB, TB)."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.2f} {units[i]}"


def get_media_info(message: Message) -> Optional[Dict[str, Any]]:
    """Extract media file metadata from a Pyrogram Message."""
    media_attrs = (
        "document",
        "video",
        "audio",
        "voice",
        "video_note",
        "animation",
        "photo",
    )

    for attr in media_attrs:
        media = getattr(message, attr, None)
        if media is not None:
            # Photos in pyrogram are a list or Photo object
            if attr == "photo":
                # For photo, take the largest one
                file_id = media.file_id
                file_size = getattr(media, "file_size", 0)
                file_name = f"photo_{message.id}.jpg"
                mime_type = "image/jpeg"
            else:
                file_id = getattr(media, "file_id", "")
                file_size = getattr(media, "file_size", 0)
                file_name = getattr(media, "file_name", None)
                mime_type = getattr(media, "mime_type", None)

                if not file_name:
                    ext = mimetypes.guess_extension(mime_type or "") or ""
                    file_name = f"{attr}_{message.id}{ext}"

                if not mime_type:
                    mime_type, _ = mimetypes.guess_type(file_name)
                    if not mime_type:
                        mime_type = "application/octet-stream"

            return {
                "media_type": attr,
                "file_id": file_id,
                "file_size": file_size,
                "file_name": file_name,
                "mime_type": mime_type,
            }

    return None


def generate_secure_hash(message_id: int) -> str:
    """Generate a quick URL-safe HMAC hash for message ID verification."""
    data = str(message_id).encode("utf-8")
    key = Config.SECRET_KEY.encode("utf-8")
    return hmac.new(key, data, hashlib.sha256).hexdigest()[:16]


def verify_secure_hash(message_id: int, hash_token: str) -> bool:
    """Verify that a given hash token matches the message ID."""
    expected_hash = generate_secure_hash(message_id)
    return hmac.compare_digest(expected_hash, hash_token)


def parse_range_header(range_header: Optional[str], file_size: int) -> Tuple[int, int]:
    """
    Parse an HTTP Range header (e.g. 'bytes=0-1048575' or 'bytes=1048576-').
    Returns (start_byte, end_byte).
    """
    if not range_header or not range_header.startswith("bytes="):
        return 0, file_size - 1

    ranges = range_header.replace("bytes=", "").split("-")
    start_str = ranges[0].strip()
    end_str = ranges[1].strip() if len(ranges) > 1 else ""

    if start_str and end_str:
        start = int(start_str)
        end = int(end_str)
    elif start_str:
        start = int(start_str)
        end = file_size - 1
    elif end_str:
        # Suffix range: -500 means the last 500 bytes
        start = max(0, file_size - int(end_str))
        end = file_size - 1
    else:
        start = 0
        end = file_size - 1

    # Clamp ranges within valid file bounds
    start = max(0, min(start, file_size - 1))
    end = max(start, min(end, file_size - 1))

    return start, end
