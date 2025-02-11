import os
import csv
import json
import subprocess
from tqdm import tqdm
from multiprocessing import Pool
from config import DOCUMENTS_FOLDER, OUTPUT_CSV, log_message
from context import load_context
from pdf_processing import extract_text_from_pdf
from doc_processing import extract_text_from_doc
from metadata_generation import generate_metadata
from file_metadata import get_file_metadata

SEMAPHORE_HELPER_SCRIPT = "semaphore-helper-single.py"  # Path to the helper script


def run_semaphore_helper(file_path):
    """Run semaphore-helper.py and return only the topic names as a list of strings."""
    try:
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
        log_message(
            f"Error running Semaphore classification for {file_path}: {e}")
        return []  # Return empty list if an error occurs


def process_document(document_file):
    """Process a single document, extracting metadata and file properties."""
    try:
        text = ""
        if document_file.endswith(".pdf"):
            text = extract_text_from_pdf(document_file)
        elif document_file.endswith((".docx", ".doc")):
            text = extract_text_from_doc(document_file)

        if not text.strip():
            log_message(
                f"No text extracted from {document_file}, skipping metadata generation.")
            return None

        dublin_core_metadata = json.loads(
            generate_metadata(text, load_context()))
        file_properties = get_file_metadata(document_file)

        # Run Semaphore classification and get only topic names
        topics = run_semaphore_helper(document_file)

        structured_metadata = {
            "Dublin Core": dublin_core_metadata,
            "Topics": topics,  # Store only topic names as a list
            "File Properties": file_properties
        }

        # Ensure format is set correctly
        if "format" not in structured_metadata["Dublin Core"]:
            structured_metadata["Dublin Core"]["format"] = structured_metadata["File Properties"].get(
                "format", "Unknown")

        validated_metadata = structured_metadata

        return {"filename": os.path.basename(document_file), "metadata": validated_metadata, "topics": topics}
    except Exception as e:
        log_message(f"Error processing {document_file}: {e}")
        return None


def main():
    """Main execution function."""
    global load_context
    context_data = load_context()

    document_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(DOCUMENTS_FOLDER)
        for file in files if file.endswith((".pdf", ".docx", ".doc"))
    ]

    log_message(f"Found {len(document_files)} documents")

    with Pool(processes=4) as pool:
        metadata_list = list(
            filter(None, pool.map(process_document, document_files)))

    fieldnames = ["filename", "metadata", "topics"]
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in metadata_list:
            formatted_metadata = json.dumps(
                entry["metadata"], indent=4, ensure_ascii=False)
            writer.writerow({
                "filename": entry["filename"],
                "metadata": formatted_metadata,  # ✅ Now formatted with newlines
                "topics": ", ".join(entry["topics"])
            })

    log_message(f"Metadata saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
