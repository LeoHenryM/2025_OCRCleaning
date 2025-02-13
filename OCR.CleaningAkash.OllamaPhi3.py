import requests
import os
import re
import requests
import time
from pathlib import Path


# Define directories
INPUT_FOLDER = Path("./data/archivesOCR/ToSendForCleaning1")
OUTPUT_FOLDER = Path("./Data/archivesCleaned/Rapport")

# Ensure output folder exists
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Get API URL (Check forwarded port dynamically!)
OLLAMA_IP = "50.214.240.91"  # Update with your latest Akash IP
OLLAMA_PORT = "30401"  # Check "Forwarded Ports" in Akash Console!
OLLAMA_URL = f"http://{OLLAMA_IP}:{OLLAMA_PORT}/api/generate"

# Ollama Model
OLLAMA_MODEL = "phi3"


def split_text_smart(text, max_length=500):
    """
    Splits text into smaller chunks (max_length), ensuring clean cut-off points.
    """
    split_texts = []
    start = 0

    while start < len(text):
        # Try to cut at a sentence boundary
        end = start + max_length
        if end >= len(text):
            split_texts.append(text[start:])
            break

        # Find the nearest period, exclamation, or newline before the cutoff
        match = re.search(r"[\.\!\?\n](?![0-9])", text[start:end][::-1])
        if match:
            end = start + max_length - match.start() - 1
        else:
            # No clean break found, just cut at max_length
            end = start + max_length

        split_texts.append(text[start:end].strip())
        start = end

    return split_texts

# Example usage:
# chunks = split_text_smart("Very long text here...", 3000)



def clean_text_with_ollama(text):
    """
    Sends a chunk of OCR text to Ollama API for cleaning.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"""Le texte suivant provient d'une reconnaissance OCR de plusieurs images d'un même document.
        Veuillez:
        1. Corriger les erreurs OCR.
        2. Couper en paragraphe si necessaire.
        3. Formater les titres en Markdown (`#` pour les niveaux).
        4. Remplacer les possibles tableau ou graphique par '[Graphique ou Tableau]'.
        5. Respecter la structure originale et ne créer pas de text qui n'existe pas.

        Texte à nettoyer :
        {text}
        """,
        "stream": False  # 🚀 Forces Ollama to return the full response at once
    }

    print(f"🔄 Sending request to {OLLAMA_URL}...")

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=600000)
        print(f"✅ Received response: {response.status_code}")

        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            print(f"❌ API Error ({response.status_code}): {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None


def process_all_reports():
    """
    Processes all merged OCR reports by sending them to Ollama in 3000-character chunks.
    """
    merged_files = list(INPUT_FOLDER.glob("*.txt"))

    for file in merged_files:
        year = file.stem  # Extract year from filename
        output_file = OUTPUT_FOLDER / f"cleaned_report.{year}.txt"

        # Skip if already processed
        if output_file.exists():
            print(f"✅ {output_file} already cleaned. Skipping.")
            continue

        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        file_conn = open(output_file, "w", encoding="utf-8")

        chunks = split_text_smart(text, 3000)
        print(f"📜 Processing {len(chunks)} chunks for {file.name}")

        for i, chunk in enumerate(chunks):
            cleaned_text = clean_text_with_ollama(chunk)
            if cleaned_text:
                file_conn.write(cleaned_text + "\n\n")

            # Respect API rate limits

            print(f"📝 {i+1}/{len(chunks)} chunks processed")

        file_conn.close()
        print(f"✅ Cleaned report saved: {output_file}")

process_all_reports()