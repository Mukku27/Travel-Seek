"""
config.py

Application configuration and environment variable loading.
"""

import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DURATION = 5

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
WEATHER_ENABLED = bool(OPENWEATHERMAP_API_KEY)
