"""Load env and expose config."""

from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL = os.getenv("BASE_URL", "https://youtubei.googleapis.com/youtubei/v1")
WEB_API_KEY = os.getenv("WEB_API_KEY", "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8")
ANDROID_API_KEY = os.getenv("ANDROID_API_KEY", "AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w")
CLIENT_VERSION = os.getenv("CLIENT_VERSION", "2.20250626.01.00")
ANDROID_VERSION = os.getenv("ANDROID_VERSION", "20.10.38")
TIMEOUT = int(os.getenv("TIMEOUT", "30"))

METADATA_HL = os.getenv("METADATA_HL", "pt")
METADATA_GL = os.getenv("METADATA_GL", "BR")

INNERTUBE_CLIENT = os.getenv("INNERTUBE_CLIENT", "WEB")
INNERTUBE_CLIENT_VERSION = os.getenv("INNERTUBE_CLIENT_VERSION", "2.20250626.01.00")
