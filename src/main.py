"""
Main Entrypoint for the NxtWave GenAI Content Systems Assessment.
Usage:
  python -m src.main --help
  python -m src.main --cli
  python -m src.main --ui
"""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    if "--ui" in sys.argv:
        from src.ui.server import start_server
        start_server()
    else:
        from src.cli import main
        main()
