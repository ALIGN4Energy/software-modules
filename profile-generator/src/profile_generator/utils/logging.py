"""
- logging.Logger
"""

import logging
import os


def setup_logging(
    run_id: str,
    level: int = logging.INFO,
    disable: bool = False,
):
    if disable:
        logging.basicConfig(level=logging.CRITICAL + 1)
        return

    filename = f"results/{run_id}.log"
    os.makedirs("results", exist_ok=True)
    format = "%(asctime)s - %(levelname)s - %(message)s"
    # Set up the root logger with basicConfig for file logging
    logging.basicConfig(
        filename=filename,
        level=level,
        format=format,
        filemode="a",  # Append mode
    )

    # Add a StreamHandler to also log to stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(format))
    logging.getLogger().addHandler(console_handler)

    return
