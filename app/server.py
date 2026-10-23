"""
FastAPI Server handling streaming, direct downloads, channel directory, and web UI.
"""

import os
import logging
import urllib.parse
from pathlib import Path
from typing import Optional, Union
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Response, status
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import Config
from app.bot import init_bot, get_stored_message, get_recent_channel_files
import app.bot as bot_module
from app.utils import (
    get_media_info,
    human_readable_size,
    parse_range_header,
)
from app.custom_streamer import byte_range_streamer

logger = logging.getLogger(__name__)

templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for starting and stopping the Telegram MTProto client."""
    logger.info("Initializing Pyrogram Bot Client...")
    client = init_bot()
    await client.start()
    bot_info = await client.get_me()
    logger.info(f"Bot successfully connected as @{bot_info.username} (ID: {bot_info.id})")
    yield
    if client.is_connected:
        logger.info("Stopping Pyrogram Bot Client...")
        await client.stop()
        logger.info("Bot client disconnected cleanly.")


app = FastAPI(title="Telegram File Streamer", lifespan=lifespan, docs_url=None, redoc_url=None)


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """Render server home landing page."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
@app.get("/ping")
async def health_check():
    """Health check endpoint for Render/Railway keep-alive pings."""
    is_conn = bot_module.bot is not None and getattr(bot_module.bot, "is_connected", False)
    return {
        "status": "healthy",
        "bot_connected": is_conn,
    }


@app.get("/channel/{channel_id}", response_class=HTMLResponse)
async def channel_directory_page(request: Request, channel_id: str):
    """Render a file directory of recent media files in a Telegram channel."""
    try:
        files = await get_recent_channel_files(channel_id)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch files from channel '{channel_id}': {e}. Ensure the bot is an Admin in the channel!",
        )

    return templates.TemplateResponse(
        request=request,
        name="channel.html",
        context={
            "channel_id": channel_id,
            "files": files,
        },
    )


@app.get("/watch/{message_id}", response_class=HTMLResponse)
@app.get("/watch/{channel_id}/{message_id}", response_class=HTMLResponse)
async def watch_page(request: Request, message_id: int, channel_id: Optional[str] = None):
    """Render the web watch and download page for a file."""
    try:
        message = await get_stored_message(message_id, chat_id=channel_id)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"File not found in channel/storage: {e}",
        )

    if not message or message.empty:
        raise HTTPException(status_code=404, detail="File message not found")

    media_info = get_media_info(message)
    if not media_info:
        raise HTTPException(status_code=400, detail="Message does not contain any downloadable media")

    file_name = media_info["file_name"]
    file_size = media_info["file_size"]
    mime_type = media_info["mime_type"]
    media_type = media_info["media_type"]

    is_video = media_type in ("video", "animation") or mime_type.startswith("video/")
    is_audio = media_type in ("audio", "voice") or mime_type.startswith("audio/")

    chat_prefix = f"/{channel_id}" if channel_id else ""
    dl_url = f"{Config.BASE_URL}/dl{chat_prefix}/{message_id}"
    stream_url = f"{Config.BASE_URL}/stream{chat_prefix}/{message_id}"
    watch_url = f"{Config.BASE_URL}/watch{chat_prefix}/{message_id}"

    return templates.TemplateResponse(
        request=request,
        name="watch.html",
        context={
            "message_id": message_id,
            "file_name": file_name,
            "file_size": file_size,
            "file_size_formatted": human_readable_size(file_size),
            "mime_type": mime_type,
            "is_video": is_video,
            "is_audio": is_audio,
            "dl_url": dl_url,
            "stream_url": stream_url,
            "watch_url": watch_url,
        },
    )


@app.get("/dl/{message_id}")
@app.get("/dl/{channel_id}/{message_id}")
async def direct_download(request: Request, message_id: int, channel_id: Optional[str] = None):
    """Direct file download with attachment header. Supports HTTP Range requests for IDM."""
    return await handle_file_stream(request, message_id, chat_id=channel_id, as_attachment=True)


@app.get("/stream/{message_id}")
@app.get("/stream/{channel_id}/{message_id}")
async def inline_stream(request: Request, message_id: int, channel_id: Optional[str] = None):
    """Inline file stream for video/audio players. Supports seekable playback via Range requests."""
    return await handle_file_stream(request, message_id, chat_id=channel_id, as_attachment=False)


async def handle_file_stream(
    request: Request,
    message_id: int,
    chat_id: Optional[str] = None,
    as_attachment: bool = False,
):
    """Core streaming logic handling Range requests, headers, and chunk generation."""
    try:
        message = await get_stored_message(message_id, chat_id=chat_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {e}")

    if not message or message.empty:
        raise HTTPException(status_code=404, detail="File message not found")

    media_info = get_media_info(message)
    if not media_info:
        raise HTTPException(status_code=400, detail="No media found in message")

    file_size = media_info["file_size"]
    file_name = media_info["file_name"]
    mime_type = media_info["mime_type"]

    range_header = request.headers.get("range")
    start, end = parse_range_header(range_header, file_size)

    content_length = (end - start) + 1

    # Safe filename header encoding for UTF-8 characters (RFC 5987)
    encoded_filename = urllib.parse.quote(file_name)
    disposition_type = "attachment" if as_attachment else "inline"
    content_disposition = (
        f'{disposition_type}; filename="{encoded_filename}"; '
        f"filename*=UTF-8''{encoded_filename}"
    )

    headers = {
        "Content-Type": mime_type,
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Disposition": content_disposition,
        "Cache-Control": "max-age=31536000, public",
    }

    status_code = status.HTTP_200_OK

    if range_header:
        status_code = status.HTTP_206_PARTIAL_CONTENT
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    return StreamingResponse(
        byte_range_streamer(
            client=bot_module.bot,
            message=message,
            start_byte=start,
            end_byte=end,
            chunk_size=Config.CHUNK_SIZE,
        ),
        status_code=status_code,
        headers=headers,
    )
