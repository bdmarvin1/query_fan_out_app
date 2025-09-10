"""
Core utilities for the Query Fan-Out Simulator.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any

def setup_logger(run_timestamp: str) -> logging.Logger:
    """
    Sets up a logger that writes to a unique, timestamped file.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_filename = log_dir / f"query-fan-out-run-{run_timestamp}.log"
    
    logger = logging.getLogger("QueryFanOutSimulator")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        fh = logging.FileHandler(log_filename)
        fh.setLevel(logging.INFO)
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
    return logger

def save_structured_data(data: Dict[str, Any], run_timestamp: str) -> Path:
    """
    Saves the captured data into a structured, timestamped JSON file.
    """
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    json_filename = output_dir / f"fan-out-data-{run_timestamp}.json"
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    return json_filename
