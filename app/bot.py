"""
Telegram Bot handlers and client manager using Pyrogram MTProto.
"""

import re
import logging
import asyncio
from typing import Optional, Union, List, Dict, Any
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from pyrogram.errors import FloodWait

from app.config import Config
from app.utils import get_media_info, human_readable_size

logger = logging.getLogger(__name__)

bot: Optional[Client] = None

# Regex for Telegram channel/message links:
# Matches: https://t.me/c/1234567890/42 or https://t.me/channel_username/42
TG_LINK_PATTERN = re.compile(
    r"(?:https?://)?(?:t\.me|telegram\.me)/(?:c/(\d+)|([a-zA-Z0-9_]+))/(\d+)"
)


def is_authorized(user_id: int) -> bool:
    """Check if the user is authorized to use the bot."""
    if not Config.AUTH_USERS:
        return True
    return user_id in Config.AUTH_USERS


def init_bot() -> Client:
    """Instantiate and register handlers on Pyrogram Client within the active event loop."""
    global bot
    if bot is not None:
        return bot

    workdir = os.environ.get("PYROGRAM_WORK_DIR", ".")

    bot = Client(
        name="TelegramFileStreamerBot",
        workdir=workdir,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        workers=Config.WORKERS,
        max_concurrent_transmissions=10,
    )

    @bot.on_message(filters.command("start") & filters.private)
    async def start_handler(client: Client, message: Message):
        if not is_authorized(message.from_user.id):
            await message.reply_text("⛔ You are not authorized to use this bot.")
            return

        welcome_text = (
            f"👋 **Hello {message.from_user.first_name}!**\n\n"
            "⚡ **Telegram High-Speed File Streamer & Server**\n\n"
            "**Two ways to use:**\n"
            "1. **Send / Forward a file** directly to me.\n"
            "2. **Send a Telegram channel post link** (e.g. `https://t.me/channel/42`).\n\n"
            "I will generate:\n"
            "• 📥 **Direct Download Link** (Multi-thread / IDM compatible)\n"
            "• 🎬 **Web Player Link** (Stream directly in your browser)\n"
            "• 📁 **Channel File Browser** (Host entire channel as a file server)\n\n"
            "✨ *Supports pause/resume, high-speed multi-connection downloads, and seeking!*"
        )

        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🌐 Open Web Server",
                        url=Config.BASE_URL,
                    )
                ]
            ]
        )
        await message.reply_text(welcome_text, reply_markup=buttons)

    @bot.on_message(filters.command("help") & filters.private)
    async def help_handler(client: Client, message: Message):
        help_text = (
            "📖 **How to Use:**\n\n"
            "• **Forward Files:** Forward any video/file from any channel to this chat.\n"
            "• **Direct Downloads:** You'll get an instant direct download link and web player.\n"
            "• **Storage Setup:** To set up your storage channel, send `/id` here or inside your channel."
        )
        await message.reply_text(help_text)

    @bot.on_message(filters.command("id"))
    async def id_handler(client: Client, message: Message):
        chat_id = message.chat.id
        if message.chat.type.name in ("CHANNEL", "SUPERGROUP", "GROUP"):
            await message.reply_text(
                f"🆔 **Channel ID:** `{chat_id}`\n\n"
                f"Copy and paste this into your `.env` file:\n"
                f"`BIN_CHANNEL={chat_id}`"
            )
        else:
            text = f"👤 **Your User ID:** `{message.from_user.id}`\n"
            if message.forward_from_chat:
                text += f"📢 **Forwarded From Channel ID:** `{message.forward_from_chat.id}`\n\n"
                text += f"Set in your `.env`:\n`BIN_CHANNEL={message.forward_from_chat.id}`\n"
            else:
                text += (
                    "\n💡 **To get your storage channel ID:**\n"
                    "1. Create a private channel in Telegram.\n"
                    "2. Add this bot as an Admin.\n"
                    "3. Forward any post from that channel to me here, or type `/id` inside the channel!"
                )
            await message.reply_text(text)

    @bot.on_message(filters.text & filters.private)
    async def link_handler(client: Client, message: Message):
        if not is_authorized(message.from_user.id):
            return

        text = message.text.strip()
        match = TG_LINK_PATTERN.search(text)
        if not match:
            if not text.startswith("/"):
                await message.reply_text(
                    "ℹ️ Send me a file or a Telegram post link like:\n"
                    "`https://t.me/c/1234567890/42` or `https://t.me/channel_name/42`"
                )
            return

        c_id, username, msg_id = match.groups()
        msg_id = int(msg_id)

        if c_id:
            chat_target: Union[int, str] = int(f"-100{c_id}")
        else:
            chat_target = username

        status_msg = await message.reply_text("⏳ *Fetching message from channel...*")

        try:
            target_msg = await client.get_messages(chat_id=chat_target, message_ids=msg_id)
            if not target_msg or target_msg.empty:
                await status_msg.edit_text("❌ Could not find this message. Make sure the bot is an Admin in the channel!")
                return

            media_info = get_media_info(target_msg)
            if not media_info:
                await status_msg.edit_text("❌ This message does not contain any downloadable media.")
                return

            chat_identifier = str(target_msg.chat.id)
            dl_url = f"{Config.BASE_URL}/dl/{chat_identifier}/{msg_id}"
            watch_url = f"{Config.BASE_URL}/watch/{chat_identifier}/{msg_id}"
            stream_url = f"{Config.BASE_URL}/stream/{chat_identifier}/{msg_id}"

            file_name = media_info["file_name"]
            file_size_formatted = human_readable_size(media_info["file_size"])

            caption = (
                f"📦 **Channel Post Found!**\n\n"
                f"📄 **Name:** `{file_name}`\n"
                f"📊 **Size:** `{file_size_formatted}`\n\n"
                f"⚡ **Direct Download:**\n`{dl_url}`\n\n"
                f"🎬 **Stream / Web Player:**\n`{watch_url}`"
            )

            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⚡ Fast Download", url=dl_url),
                        InlineKeyboardButton("🎬 Watch / Stream", url=watch_url),
                    ],
                    [
                        InlineKeyboardButton("🔗 Copy Raw Stream URL", copy_text=stream_url),
                    ],
                ]
            )

            await status_msg.edit_text(caption, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Error fetching channel post: {e}")
            await status_msg.edit_text(
                f"❌ **Error accessing channel post:**\n`{e}`\n\n"
                f"Make sure @domonsddbot is added as an **Admin** to that channel!"
            )

    @bot.on_message(
        (
            filters.document
            | filters.video
            | filters.audio
            | filters.voice
            | filters.video_note
            | filters.animation
            | filters.photo
        )
        & filters.private
    )
    async def media_handler(client: Client, message: Message):
        if not is_authorized(message.from_user.id):
            await message.reply_text("⛔ You are not authorized to use this bot.")
            return

        media_info = get_media_info(message)
        if not media_info:
            await message.reply_text("❌ Unsupported media type.")
            return

        if not Config.BIN_CHANNEL:
            await message.reply_text(
                "⚠️ **BIN_CHANNEL is not set in .env!**\n\n"
                "To store and stream uploaded files:\n"
                "1. Create a private channel in Telegram.\n"
                "2. Add `@domonsddbot` as an Administrator.\n"
                "3. Get the Channel ID (starts with `-100`) and set `BIN_CHANNEL=-100xxxxxxxxxx` in `.env`.\n"
                "4. Restart the app."
            )
            return

        status_msg = await message.reply_text("⏳ *Generating high-speed link...*")

        try:
            forwarded_msg = await message.copy(chat_id=Config.BIN_CHANNEL)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            forwarded_msg = await message.copy(chat_id=Config.BIN_CHANNEL)
        except Exception as e:
            logger.error(f"Error copying message to BIN_CHANNEL: {e}")
            await status_msg.edit_text(
                f"❌ **Failed to store file in BIN_CHANNEL.**\n"
                f"Please make sure the bot is an **Admin** in channel `{Config.BIN_CHANNEL}` with Post Messages permission.\n\n"
                f"`Error: {e}`"
            )
            return

        msg_id = forwarded_msg.id
        file_name = media_info["file_name"]
        file_size_formatted = human_readable_size(media_info["file_size"])
        media_type = media_info["media_type"].capitalize()

        dl_url = f"{Config.BASE_URL}/dl/{msg_id}"
        watch_url = f"{Config.BASE_URL}/watch/{msg_id}"
        stream_url = f"{Config.BASE_URL}/stream/{msg_id}"

        caption = (
            f"📦 **File Stored Successfully!**\n\n"
            f"📄 **Name:** `{file_name}`\n"
            f"📊 **Size:** `{file_size_formatted}`\n"
            f"🏷 **Type:** `{media_type}`\n\n"
            f"⚡ **Direct Download:**\n`{dl_url}`\n\n"
            f"🎬 **Stream / Web Player:**\n`{watch_url}`"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⚡ Fast Download", url=dl_url),
                    InlineKeyboardButton("🎬 Watch / Stream", url=watch_url),
                ],
                [
                    InlineKeyboardButton("🔗 Copy Raw Stream URL", copy_text=stream_url),
                ],
            ]
        )

        await status_msg.edit_text(caption, reply_markup=keyboard)

    return bot


async def get_stored_message(message_id: int, chat_id: Optional[Union[int, str]] = None) -> Message:
    """Retrieve message from storage BIN_CHANNEL or a specified chat/channel."""
    global bot
    if bot is None:
        init_bot()
    target_chat = chat_id if chat_id is not None else Config.BIN_CHANNEL
    if isinstance(target_chat, str) and (target_chat.startswith("-") or target_chat.isdigit()):
        target_chat = int(target_chat)
    return await bot.get_messages(chat_id=target_chat, message_ids=message_id)


async def get_recent_channel_files(chat_id: Union[int, str], limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent media files from a channel to display as a file directory."""
    global bot
    if bot is None:
        init_bot()
    target_chat = chat_id
    if isinstance(target_chat, str) and (target_chat.startswith("-") or target_chat.isdigit()):
        target_chat = int(target_chat)

    files = []
    async for msg in bot.get_chat_history(chat_id=target_chat, limit=limit):
        media_info = get_media_info(msg)
        if media_info:
            files.append({
                "message_id": msg.id,
                "file_name": media_info["file_name"],
                "file_size": media_info["file_size"],
                "file_size_formatted": human_readable_size(media_info["file_size"]),
                "mime_type": media_info["mime_type"],
                "media_type": media_info["media_type"],
                "date": msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else "",
                "watch_url": f"{Config.BASE_URL}/watch/{target_chat}/{msg.id}",
                "dl_url": f"{Config.BASE_URL}/dl/{target_chat}/{msg.id}",
            })
    return files
