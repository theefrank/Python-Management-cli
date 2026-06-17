"""File storage utilities for project data with comprehensive error handling."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from models.entities import User

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT_DIR / "data.json"


def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_data() -> dict[str, Any]:
    """Load user data from JSON file with comprehensive error handling."""
    if not DATA_FILE.exists():
        logger.info(f"Data file not found at {DATA_FILE}. Returning empty data.")
        return {"users": []}

    try:
        with DATA_FILE.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
            logger.info(f"Successfully loaded data from {DATA_FILE}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {DATA_FILE}: {e}. Returning empty data.")
        return {"users": []}
    except IOError as e:
        logger.error(f"IO error reading {DATA_FILE}: {e}. Returning empty data.")
        return {"users": []}
    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}. Returning empty data.")
        return {"users": []}

    try:
        users = [User.from_dict(user_data) for user_data in raw.get("users", [])]
        return {"users": users}
    except Exception as e:
        logger.error(f"Error parsing user data: {e}. Returning empty data.")
        return {"users": []}


def save_data(data: dict[str, Any]) -> bool:
    """Save user data to JSON file with comprehensive error handling."""
    try:
        serializable = {"users": [user.to_dict() for user in data["users"]]}

        with DATA_FILE.open("w", encoding="utf-8") as handle:
            json.dump(serializable, handle, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved data to {DATA_FILE}")
        return True
    except IOError as e:
        logger.error(f"IO error writing to {DATA_FILE}: {e}")
        return False
    except TypeError as e:
        logger.error(f"Serialization error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving data: {e}")
        return False


def backup_data() -> bool:
    """Create a backup of the current data file."""
    if not DATA_FILE.exists():
        logger.info("No data file to backup.")
        return True

    try:
        backup_file = DATA_FILE.with_suffix(".backup.json")
        with DATA_FILE.open("r", encoding="utf-8") as original:
            with backup_file.open("w", encoding="utf-8") as backup:
                backup.write(original.read())
        logger.info(f"Data backed up to {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False