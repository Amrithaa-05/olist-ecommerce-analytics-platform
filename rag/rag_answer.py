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
# Get User Question
# ============================================================

question = input("Ask a question about the project: ").strip()


# ============================================================
# Create Question Embedding
# ============================================================

embedding_response = ollama.embed(
    model="nomic-embed-text",
    input=question
)

question_embedding = embedding_response["embeddings"][0]


# ============================================================
# Retrieve Relevant Knowledge
# ============================================================

results = collection.query(
    query_embeddings=[question_embedding],
    n_results=3
)

documents = results["documents"][0]


# ============================================================
# Combine Retrieved Knowledge
# ============================================================

context = "\n\n".join(documents)


# ============================================================
# Send Question + Context to Qwen
# ============================================================

system_prompt = """
You are the AI Business Assistant for the
E-Commerce Supply Chain & Customer Analytics Platform.

Answer the user's question using the provided project
knowledge.

Rules:

1. Use the retrieved project knowledge as your primary source.

2. Do not invent project facts, statistics, features,
   or implementation details.

3. If the retrieved knowledge does not contain enough
   information to answer the question, clearly say that
   the project knowledge base does not contain enough
   information.

4. Give a clear and concise answer.

5. Explain technical concepts in simple language.

6. Do not mention embeddings, vector databases,
   similarity search, or internal RAG processing
   unless the user specifically asks about them.
"""


user_prompt = f"""
Project knowledge:

{context}

User question:

{question}
"""


response = ollama.chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]
)


# ============================================================
# Display Answer
# ============================================================

print("\nAI Assistant Answer:\n")
print(response.message.content)