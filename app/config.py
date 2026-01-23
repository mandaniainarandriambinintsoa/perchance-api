import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_VERSION = "v1"
API_TITLE = "Artigen API"
API_DESCRIPTION = "Free AI Image Generator API using Pollinations.ai"

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Default generation settings
DEFAULT_RESOLUTION = "1024x1024"
DEFAULT_STYLE = "realistic"

# Pollinations.ai API Token (optional, for premium features like img2img with kontext)
POLLINATIONS_TOKEN = os.getenv("POLLINATIONS_TOKEN", "")
