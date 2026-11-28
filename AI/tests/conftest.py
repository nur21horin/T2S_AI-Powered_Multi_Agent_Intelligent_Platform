"""Test configuration for AI module tests."""
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set test environment variables before importing AI modules
os.environ.setdefault("AI_ENABLE_MOCK_LLM", "true")
os.environ.setdefault("GROQ_API_KEY", "test-key-for-mocking")
os.environ.setdefault("LLM_TEMPERATURE", "0.0")

# Clear settings cache after setting env vars
from AI.config import clear_settings_cache
clear_settings_cache()