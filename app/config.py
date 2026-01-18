import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_VERSION = "v1"
API_TITLE = "Perchance Character Generator API"
API_DESCRIPTION = "API wrapper for Perchance.org AI character generation"

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Rate Limiting (for future implementation)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

# Default generation settings
DEFAULT_RESOLUTION = "512x768"
DEFAULT_STYLE = "anime"
