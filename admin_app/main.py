"""
Upbeat Attendance — Admin Application Entry Point.
"""
import logging
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from admin_app.config import APP_NAME, APP_VERSION, LOG_DIR

# Configure logging
log_file = LOG_DIR / "admin_app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def main():
    """Launch the Admin Management Application."""
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

    try:
        from admin_app.ui.app import AdminApp

        app = AdminApp()
        app.mainloop()

    except Exception as e:
        logger.critical(f"Fatal error starting Admin Application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
