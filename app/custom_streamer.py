"""
High-speed chunk generator supporting HTTP Range requests directly over Telegram MTProto.
Includes an asynchronous prefetch buffer to eliminate latency between Telegram DC chunk requests.
"""

import math
import asyncio
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
    Uses an asynchronous producer-consumer queue to prefetch upcoming chunks from Telegram MTProto
    in parallel while the HTTP server streams the current chunk to the client.
    """
    start_chunk = start_byte // chunk_size
    end_chunk = end_byte // chunk_size
    chunks_to_fetch = (end_chunk - start_chunk) + 1

    # Prefetch buffer to keep network pipeline saturated
    queue: asyncio.Queue = asyncio.Queue(maxsize=4)
    sentinel = object()

    async def producer():
        try:
            async for chunk in client.stream_media(
                message,
                offset=start_chunk,
                limit=chunks_to_fetch,
            ):
                await queue.put(chunk)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            await queue.put(e)
        finally:
            await queue.put(sentinel)

    producer_task = asyncio.create_task(producer())
    current_chunk_index = start_chunk

    try:
        while True:
            chunk = await queue.get()
            if chunk is sentinel:
                break
            if isinstance(chunk, Exception):
                raise chunk

            chunk_len = len(chunk)
            if chunk_len == 0:
                break

            chunk_start_byte = current_chunk_index * chunk_size
            chunk_end_byte = chunk_start_byte + chunk_len - 1

            if chunk_end_byte >= start_byte and chunk_start_byte <= end_byte:
                slice_start = max(0, start_byte - chunk_start_byte)
                slice_end = min(chunk_len, (end_byte - chunk_start_byte) + 1)
                yield chunk[slice_start:slice_end]

            current_chunk_index += 1
    finally:
        if not producer_task.done():
            producer_task.cancel()
