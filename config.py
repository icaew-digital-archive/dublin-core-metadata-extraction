import json
import logging
import os
import subprocess

from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key. Please set it in the .env file.")

# OpenAI API Configuration
OPENAI_MODEL = "gpt-4o"  # Change to "gpt-4-turbo" or another model if needed

# Paths
DOCUMENTS_FOLDER = "/home/digital-archivist/Documents/custom scripts/dublin-core-metadata-extraction/test-and-output-files/small-batch"
OUTPUT_CSV = "/home/digital-archivist/Documents/custom scripts/dublin-core-metadata-extraction/test-and-output-files/metadata_output.csv"
LOG_FILE = "/home/digital-archivist/Documents/custom scripts/dublin-core-metadata-extraction/test-and-output-files/metadata_extraction.log"


# Metadata standard selection: "dublin_core", "marc21"
METADATA_STANDARD = "dublin_core"  # Change to "dublin_core", "marc21"


# Logging configuration
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_message(message):
    logger.info(message)
    print(message)


METADATA_CONTEXT_FILE = os.path.join(os.path.dirname(__file__), "context.json")

# Enable or disable custom classification (can be Semaphore or another method)
USE_CUSTOM_CLASSIFICATION = True  # Set to False to disable classification


def custom_classification(file_path):
    """User-defined classification function. Default: Uses Semaphore."""
    try:
        SEMAPHORE_HELPER_SCRIPT = "semaphore-helper-single.py"
        result = subprocess.run(
            ["python3", SEMAPHORE_HELPER_SCRIPT, file_path],
            capture_output=True,
            text=True,
            check=True
        )
        semaphore_output = json.loads(result.stdout)

        # Extract only topic names, ensuring we get strings and not dicts
        return [topic["topic"] if isinstance(topic, dict) else topic for topic in semaphore_output.get("topics", [])]
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        log_message(f"Error running classification for {file_path}: {e}")
        return []  # Return empty list if an error occurs
