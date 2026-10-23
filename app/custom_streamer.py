"""
High-speed chunk generator supporting HTTP Range requests directly over Telegram MTProto.
"""

import math
from typing import AsyncGenerator
from pyrogram import Client
from pyrogram.types import Message


async def byte_range_streamer(
    client: Client,
    message: Message,
    start_byte: int,
    end_byte: int,
    chunk_size: int = 1024 * 1024,
) -> AsyncGenerator[bytes, None]:
    """
    Stream bytes directly from Telegram MTProto matching an exact [start_byte, end_byte] range.
    Uses Telegram's native chunk-level offsets (1 MiB chunks) to skip unnecessary data
    and byte-slices the boundary chunks with zero overhead.
    """
    # Calculate chunk offsets
    start_chunk = start_byte // chunk_size
    end_chunk = end_byte // chunk_size
    chunks_to_fetch = (end_chunk - start_chunk) + 1

    current_chunk_index = start_chunk

    async for chunk in client.stream_media(
        message,
        offset=start_chunk,
        limit=chunks_to_fetch,
    ):
        chunk_len = len(chunk)
        if chunk_len == 0:
            break

        chunk_start_byte = current_chunk_index * chunk_size
        chunk_end_byte = chunk_start_byte + chunk_len - 1

        # Check overlap with requested range
        if chunk_end_byte < start_byte:
            current_chunk_index += 1
            continue

        if chunk_start_byte > end_byte:
            break

        # Slicing within this chunk
        slice_start = max(0, start_byte - chunk_start_byte)
        slice_end = min(chunk_len, (end_byte - chunk_start_byte) + 1)

        yield chunk[slice_start:slice_end]

        current_chunk_index += 1
