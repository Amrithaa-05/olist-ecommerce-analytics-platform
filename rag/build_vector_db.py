import chromadb
import json
from pathlib import Path


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

EMBEDDINGS_FILE = BASE_DIR / "embeddings.json"
VECTOR_DB_DIR = BASE_DIR / "chroma_db"


# ============================================================
# Load Embeddings
# ============================================================

with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as file:
    embedded_chunks = json.load(file)


print(f"Loaded {len(embedded_chunks)} embedded chunks.")


# ============================================================
# Create ChromaDB Client
# ============================================================

client = chromadb.PersistentClient(
    path=str(VECTOR_DB_DIR)
)


# ============================================================
# Create Collection
# ============================================================

collection = client.get_or_create_collection(
    name="olist_project_knowledge"
)


# ============================================================
# Prepare Data
# ============================================================

ids = []
documents = []
embeddings = []

for chunk in embedded_chunks:

    ids.append(str(chunk["id"]))
    documents.append(chunk["text"])
    embeddings.append(chunk["embedding"])


# ============================================================
# Store in ChromaDB
# ============================================================

collection.upsert(
    ids=ids,
    documents=documents,
    embeddings=embeddings
)


# ============================================================
# Verify
# ============================================================

count = collection.count()

print()
print("Vector database created successfully.")
print(f"Stored documents: {count}")
print(f"Database location: {VECTOR_DB_DIR}")