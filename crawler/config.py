import os
import re
from dotenv import load_dotenv

load_dotenv()

class Config:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    _RAW_GITHUB_TOKENS = os.getenv("CUSTOM_GITHUB_TOKENS")
    if _RAW_GITHUB_TOKENS:
        GITHUB_TOKENS = [t for t in re.split(r"[,\s;]+", _RAW_GITHUB_TOKENS) if t]
    else:
        GITHUB_TOKENS = [GITHUB_TOKEN] if GITHUB_TOKEN else []
    GITHUB_REQUEST_DELAY = float(os.getenv("GITHUB_REQUEST_DELAY", "0.3"))
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # S3 / R2 Configuration
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
    S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "ai-trending-data")
    S3_REGION_NAME = os.getenv("S3_REGION_NAME", "auto")
    
    # Paths
    DATA_DIR = "data"
