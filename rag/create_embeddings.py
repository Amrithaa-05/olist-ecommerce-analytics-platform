import ollama
from pathlib import Path
import json


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

KNOWLEDGE_FILE = BASE_DIR / "project_knowledge.md"
OUTPUT_FILE = BASE_DIR / "embeddings.json"


# ============================================================
# Read Knowledge Base
# ============================================================

with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as file:
    text = file.read()


# ============================================================
# Split Knowledge into Chunks
# ============================================================

sections = text.split("\n## ")

chunks = []

for section in sections:

    section = section.strip()

    if section:
        if not section.startswith("#"):
            section = "## " + section

        chunks.append(section)


print(f"Knowledge base loaded.")
print(f"Number of chunks: {len(chunks)}")


# ============================================================
# Generate Embeddings
# ============================================================

embedded_chunks = []

for index, chunk in enumerate(chunks, start=1):

    print(f"Creating embedding {index}/{len(chunks)}...")

    response = ollama.embed(
        model="nomic-embed-text",
        input=chunk
    )

    embedding = response["embeddings"][0]

    embedded_chunks.append(
        {
            "id": index,
            "text": chunk,
            "embedding": embedding
        }
    )


# ============================================================
# Save Embeddings
# ============================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as file:

    json.dump(
        embedded_chunks,
        file
    )


print()
print("Embedding generation completed.")
print(f"Saved to: {OUTPUT_FILE}")