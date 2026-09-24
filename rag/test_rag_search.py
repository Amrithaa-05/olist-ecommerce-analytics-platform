import chromadb
import ollama
from pathlib import Path


# ============================================================
# Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

VECTOR_DB_DIR = BASE_DIR / "chroma_db"


# ============================================================
# Connect to ChromaDB
# ============================================================

client = chromadb.PersistentClient(
    path=str(VECTOR_DB_DIR)
)

collection = client.get_collection(
    name="olist_project_knowledge"
)


# ============================================================
# User Question
# ============================================================

question = input("Ask a question about the project: ")


# ============================================================
# Convert Question into Embedding
# ============================================================

response = ollama.embed(
    model="nomic-embed-text",
    input=question
)

question_embedding = response["embeddings"][0]


# ============================================================
# Search Vector Database
# ============================================================

results = collection.query(
    query_embeddings=[question_embedding],
    n_results=3
)


# ============================================================
# Display Retrieved Knowledge
# ============================================================

print("\nRetrieved knowledge:\n")

documents = results["documents"][0]

for index, document in enumerate(documents, start=1):

    print(f"--- Result {index} ---")
    print(document)
    print()