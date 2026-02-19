"""Load env and expose config."""

from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL = os.getenv("BASE_URL", "https://youtubei.googleapis.com/youtubei/v1")
WEB_API_KEY = os.getenv("WEB_API_KEY")
ANDROID_API_KEY = os.getenv("ANDROID_API_KEY")

if not WEB_API_KEY:
    raise RuntimeError(
        "WEB_API_KEY is required. Set it in .env (copy from .env.example). "
        "YouTube InnerTube keys are public/rotating but must not be hardcoded."
    )
if not ANDROID_API_KEY:
    raise RuntimeError(
        "ANDROID_API_KEY is required. Set it in .env (copy from .env.example). "
        "YouTube InnerTube keys are public/rotating but must not be hardcoded."
    )
CLIENT_VERSION = os.getenv("CLIENT_VERSION", "2.20250626.01.00")
ANDROID_VERSION = os.getenv("ANDROID_VERSION", "20.10.38")
TIMEOUT = int(os.getenv("TIMEOUT", "30"))
TIMEOUT_CHANNEL = int(os.getenv("TIMEOUT_CHANNEL", "300"))  # 5 min for channel processing

METADATA_HL = os.getenv("METADATA_HL", "pt")
METADATA_GL = os.getenv("METADATA_GL", "BR")

INNERTUBE_CLIENT = os.getenv("INNERTUBE_CLIENT", "WEB")
INNERTUBE_CLIENT_VERSION = os.getenv("INNERTUBE_CLIENT_VERSION", "2.20250626.01.00")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
GEMINI_COST_PER_1M_INPUT = float(os.getenv("GEMINI_COST_PER_1M_INPUT", "0.10"))
GEMINI_COST_PER_1M_OUTPUT = float(os.getenv("GEMINI_COST_PER_1M_OUTPUT", "0.40"))
