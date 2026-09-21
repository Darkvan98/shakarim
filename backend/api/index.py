import sys
import os

# Add the project root to sys.path so that "backend.app" is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.app.main import app  # noqa: E402

# Vercel expects a variable named `app` or `handler`
handler = app
