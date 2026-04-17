"""
Universal Dev Environment Manager — main entry point.

Usage:
    python main.py              # Normal launch
    python main.py --elevate    # Request admin/UAC elevation (Windows)
"""

import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import logger, is_windows, is_admin, request_admin
from gui import ManagerApp


def main():
    logger.info("═══ Universal Dev Environment Manager started ═══")

    if is_windows() and not is_admin():
        if "--elevate" in sys.argv:
            logger.info("Requesting UAC elevation…")
            try:
                request_admin()
            except Exception:
                logger.warning("UAC elevation failed — continuing without admin.")
        else:
            logger.warning(
                "Running without admin privileges. "
                "Some installations may need admin. "
                "Relaunch with --elevate for full access."
            )

    app = ManagerApp()
    app.run()


if __name__ == "__main__":
    main()
