# ⚡ Telegram High-Speed File Streamer & Web Server

A high-performance file server and streaming web application that converts any Telegram file into a direct, high-speed HTTP download link and an online media player.

Forward or upload any file to your Telegram Bot, and it generates:
- 📥 **Direct Download Link**: Multi-thread enabled, IDM / aria2 / curl compatible.
- 🎬 **Web Player & Watch Page**: Stream seekable video/audio in browser with zero buffering delays.
- 📋 **Permanent Storage**: Files are safely mirrored to a private storage channel.

---

## 🚀 Key Features

- **Maximum Telegram Download Speeds**: Leverages Telegram MTProto with `TgCrypto` (C-optimized AES cryptography).
- **HTTP Range Requests (206 Partial Content)**:
  - Seek to any second in videos without waiting for the whole file to download.
  - Multi-connection downloading with **Internet Download Manager (IDM)**, **aria2**, or download managers.
  - Resume broken or paused downloads.
- **Sleek Web Interface**: Modern, responsive dark-mode UI with embedded HTML5 video/audio player and 1-click clipboard actions.
- **Cloud & Docker Ready**: Easy 1-click deployment on **Render**, **Railway**, **Koyeb**, or any **Docker/VPS** host.
- **Access Control**: Optional `AUTH_USERS` whitelist to restrict bot usage to you and your friends.
- **Auto Keep-Alive**: Built-in background pinging to prevent free cloud tiers (like Render) from sleeping.

---

## 🛠️ Prerequisites

Before running the application, you need 3 Telegram credentials:

### 1. `API_ID` and `API_HASH`
1. Log in to [my.telegram.org](https://my.telegram.org) with your phone number.
2. Click on **API development tools**.
3. Create a new app (any title/short name) and copy your `api_id` and `api_hash`.

### 2. `BOT_TOKEN`
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, choose a name and username.
3. Copy the HTTP API token provided.

### 3. `BIN_CHANNEL` (Storage Channel)
1. In Telegram, create a **New Channel** (set it to **Private**).
2. Add your newly created bot as an **Administrator** in this channel with **Post Messages** permission.
3. Get the Channel ID:
   - Forward any message from this channel to [@userinfobot](https://t.me/userinfobot) or [@RoseBot](https://t.me/MissRose_bot).
   - Channel IDs start with `-100` (e.g. `-1001234567890`).

---

## 💻 Running Locally

### Step 1: Clone or navigate to the directory
```powershell
cd C:\Users\Zayn\.gemini\antigravity\scratch\telegram-file-streamer
```

### Step 2: Install dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure `.env`
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` and fill in your values:
```ini
API_ID=12345678
API_HASH=abcdef0123456789abcdef0123456789
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BIN_CHANNEL=-1001234567890
BASE_URL=http://localhost:8000
```

### Step 4: Run the server
```powershell
python main.py
```
Visit `http://localhost:8000` in your web browser.

> **Tip for sharing with friends from your local PC**:
> You can expose your local server to the internet using Cloudflare Tunnel or ngrok:
> ```bash
> cloudflared tunnel --url http://localhost:8000
> ```
> Then set `BASE_URL` in `.env` to the public Cloudflare URL!

---

## ☁️ Deploying for Free to Cloud (Render / Railway / VPS)

> **Why not Vercel?**
> Vercel is a serverless platform with a 10–60 second maximum execution timeout. Downloading or streaming a 500MB–2GB file over serverless functions will crash with a `FUNCTION_INVOCATION_TIMEOUT`. Platforms like **Render**, **Railway**, **Koyeb**, or a **VPS** run persistent Python servers and have no file size or duration streaming limits!

### Option A: Deploy to Render (Recommended Free Cloud Host)

1. Push this project folder to your GitHub account as a new repository.
2. Sign up or log into [Render.com](https://render.com).
3. Click **New +** -> **Web Service**.
4. Connect your GitHub repository.
5. Set:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
6. Under **Advanced** -> **Add Environment Variable**, set:
   - `API_ID`: Your API ID
   - `API_HASH`: Your API Hash
   - `BOT_TOKEN`: Your Bot Token
   - `BIN_CHANNEL`: Your Channel ID (e.g. `-1001234567890`)
   - `BASE_URL`: `https://your-service-name.onrender.com` (Render URL)
   - `PORT`: `8000`
7. Click **Create Web Service**.

---

### Option B: Deploy with Docker

```bash
# Build the Docker image
docker build -t telegram-file-streamer .

# Run container with environment file
docker run -d --name tg-streamer -p 8000:8000 --env-file .env telegram-file-streamer
```

Or using Docker Compose:
```bash
docker compose up -d
```

---

## 📖 How to Use

1. Open Telegram and start a chat with your bot.
2. Send or forward any video, audio, software archive, or document.
3. The bot immediately replies with:
   - ⚡ **Direct Download Link**: `https://your-domain.com/dl/{message_id}` (Triggers immediate file download)
   - 🎬 **Watch / Stream Link**: `https://your-domain.com/watch/{message_id}` (Opens responsive web player)
   - 🔗 **Raw Stream URL**: `https://your-domain.com/stream/{message_id}` (For VLC or media players)
4. Send the link to your friend — they can download it directly at maximum bandwidth!

---

## 🔒 Security & Access Control

- **Restrict Bot Access**: Set `AUTH_USERS` in `.env` to your Telegram User ID (and your friends' IDs, separated by commas). Anyone else who sends messages to the bot will be rejected.
- **Keep-Alive**: If deployed on Render free tier, the application pings itself every 5 minutes to stay awake.
