"""
pytest configuration — no external services needed for unit tests.
"""
import sys
import os

# Ensure backend/ is on the path so imports work without pip install -e
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
