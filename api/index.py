"""
Vercel Serverless Entrypoint.
Exposes the FastAPI ASGI application for @vercel/python.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path so 'app' can be imported
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Ensure writable session directory for AWS Lambda / Vercel
os.environ.setdefault("PYROGRAM_WORK_DIR", "/tmp")

from app.server import app
