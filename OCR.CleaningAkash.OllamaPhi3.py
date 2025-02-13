import requests
import os
import time
import re
from pathlib import Path

# ✅ GitHub Links
RAW_TEXT_URL = "https://raw.githubusercontent.com/LeoHenryM/2025_OCRCleaning/refs/heads/main/ToSendForCleaning1/rapport_PF_1946.txt"  # Change to actual file
OUTPUT_REPO = "https://github.com/LeoHenryM/2025_OCRCleaning"  # Change if needed

# ✅ Fetch Latest IP & Port from Environment
OLLAMA_IP = os.getenv("OLLAMA_IP", "50.214.240.91")  # Update if needed
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "30401")  # Change if Akash assigns a new one
OLLAMA_URL = f"http://{OLLAMA_IP}:{OLLAMA_PORT}/api/generate"
OLLAMA_MODEL = "phi3"


# ✅ Fetch Text File from GitHub
def fetch_text_from_github():
    print("📥 Downloading text from GitHub...")
    response = requests.get(RAW_TEXT_URL)
    if response.status_code == 200:
        return response.text
    else:
        print(f"❌ Error fetching text: {response.status_code}")
        return None


# ✅ Smart Text Split
def split_text_smart(text, max_length=3000):
    split_texts = []
    start = 0
    while start < len(text):
        end = start + max_length
        if end >= len(text):
            split_texts.append(text[start:])
            break
        match = re.search(r"[\.\!\?\n](?![0-9])", text[start:end][::-1])
        end = start + max_length - match.start() - 1 if match else start + max_length
        split_texts.append(text[start:end].strip())
        start = end
    return split_texts


# ✅ Ollama Cleaning Function
def clean_text_with_ollama(text):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"""Le texte suivant provient d'une reconnaissance OCR de plusieurs images d'un même document.
        Veuillez:
        1. Corriger les erreurs OCR.
        2. Ajouter des paragraphes.
        3. Formater les titres en Markdown (`#` pour les niveaux).
        4. Remplacer les tableaux/graphes par '[Graphique ou Tableau]'.
        5. Respecter la structure originale.

        Texte à nettoyer :
        {text}
        """,
        "stream": False
    }
    print(f"🔄 Sending request to {OLLAMA_URL}...")
    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    if response.status_code == 200:
        return response.json().get("response", "").strip()
    else:
        print(f"❌ API Error ({response.status_code}): {response.text}")
        return None


# ✅ Process the Text
def process_text():
    text = fetch_text_from_github()
    if not text:
        return

    chunks = split_text_smart(text, 3000)
    cleaned_text = []

    print(f"📜 Processing {len(chunks)} chunks...")
    for i, chunk in enumerate(chunks):
        cleaned = clean_text_with_ollama(chunk)
        if cleaned:
            cleaned_text.append(cleaned)
        print(f"✅ {i + 1}/{len(chunks)} chunks processed")

    final_text = "\n\n".join(cleaned_text)

    # Save locally
    output_path = "cleaned_text.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_text)

    print("✅ Cleaning complete. Uploading to GitHub...")
    upload_to_github(output_path)


# ✅ Upload to GitHub
def upload_to_github(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    payload = {
        "message": "Updated OCR cleaned file",
        "content": content.encode("utf-8").hex(),
        "branch": "main"
    }

    headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN', '')}"}
    response = requests.put(f"{OUTPUT_REPO}/contents/cleaned_text.txt", json=payload, headers=headers)

    if response.status_code in [200, 201]:
        print("✅ Uploaded successfully!")
    else:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")


# ✅ Run the Process
process_text()
