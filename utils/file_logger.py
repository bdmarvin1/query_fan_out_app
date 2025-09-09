"""
Core utilities for the Query Fan-Out Simulator.

This module provides robust logging and structured data persistence functionalities.
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

def setup_logger() -> logging.Logger:
    """
    Sets up and returns a logger instance that writes to a unique, timestamped file.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_filename = log_dir / f"query-fan-out-run-{timestamp}.log"
    
    logger = logging.getLogger("QueryFanOutSimulator")
    logger.setLevel(logging.INFO)
    
    # Avoid adding handlers if they already exist
    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(log_filename)
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(fh)
        logger.addHandler(ch)
        
    return logger

def save_structured_data(data: Dict[str, Any]) -> Path:
    """
    Saves the captured data from all stages into a single, structured JSON file.
    
    Args:
        data: A dictionary containing all the data to be saved.
        
    Returns:
        The path to the saved JSON file.
    """
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_filename = output_dir / f"fan-out-data-{timestamp}.json"
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    return json_filename
