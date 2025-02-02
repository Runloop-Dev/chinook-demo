import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    DEVBOX_ID = os.environ.get('DEVBOX_ID')
    RUNLOOP_API_KEY = os.environ.get('RUNLOOP_API_KEY')
    MCP_FILES_DIR = Path(__file__).parent / 'mcp'