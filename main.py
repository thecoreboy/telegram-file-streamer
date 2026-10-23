"""
Main application entry point.
Starts Uvicorn server which manages the FastAPI application and Pyrogram lifecycle.
"""

import sys
import logging
import uvicorn
from app.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("Main")


def main():
    if not Config.API_ID or not Config.API_HASH or not Config.BOT_TOKEN:
        logger.error(
            "CRITICAL: API_ID, API_HASH, or BOT_TOKEN is missing! Please configure them in .env"
        )
        sys.exit(1)

    if not Config.BIN_CHANNEL:
        logger.warning(
            "NOTE: BIN_CHANNEL is not set in .env. Uploading files directly to the bot in private requires a BIN_CHANNEL. Direct channel link streaming and /channel/{id} directory browsing will still work!"
        )

    logger.info(f"Starting server on http://{Config.HOST}:{Config.PORT}")
    logger.info(f"Public Base URL: {Config.BASE_URL}")

    uvicorn.run(
        "app.server:app",
        host=Config.HOST,
        port=Config.PORT,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
