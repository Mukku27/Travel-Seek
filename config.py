"""
config.py

Application configuration and environment variable loading.
"""

import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DURATION = 5

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
MCP_ENABLED = bool(GOOGLE_MAPS_API_KEY)
