"""
Core utilities for the Query Fan-Out Simulator, including logging and data persistence.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict


def setup_logger(run_timestamp: str) -> logging.Logger:
    """
    Sets up a logger that writes to both a timestamped file and the console.

    Args:
        run_timestamp: The timestamp for the current run, used for unique filenames.

    Returns:
        A configured logger instance.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_filename = log_dir / f"query-fan-out-run-{run_timestamp}.log"

    logger = logging.getLogger("QueryFanOutSimulator")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # File handler for logging to a file
        fh = logging.FileHandler(log_filename)
        fh.setLevel(logging.INFO)

        # Stream handler for logging to the console
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Formatter for log messages
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger


def save_structured_data(data: Dict[str, Any], run_timestamp: str) -> Path:
    """
    Saves the captured data into a structured, timestamped JSON file.

    Args:
        data: The dictionary containing the data to be saved.
        run_timestamp: The timestamp for the current run, used for unique filenames.

    Returns:
        The path to the newly created JSON file.
    """
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    json_filename = output_dir / f"fan-out-data-{run_timestamp}.json"

    with open(json_filename, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4)

    return json_filename
