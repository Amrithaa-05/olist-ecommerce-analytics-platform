from fastapi import FastAPI
from pydantic import BaseModel, Field
import joblib
import pandas as pd
from pathlib import Path
import ollama
import mysql.connector
import chromadb
from dotenv import load_dotenv
import os
import re


# ============================================================
# Application Setup
# ============================================================

app = FastAPI(title="E-Commerce Analytics API")

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# ============================================================
# Load Delivery Prediction Model
# ============================================================

model = joblib.load(
    BASE_DIR / "delivery_delay_model.pkl"
)

feature_columns = joblib.load(
    BASE_DIR / "delivery_model_features.pkl"
)


# ============================================================
# MySQL Connection
# ============================================================

def get_db_connection():
    password = os.getenv("MYSQL_PASSWORD")

    return mysql.connector.connect(
        host="127.0.0.1",
        port=3307,
        user="root",
        password=password,
        database="olist_db"
    )


# ============================================================
# ChromaDB Setup
# ============================================================

VECTOR_DB_DIR = BASE_DIR / "rag" / "chroma_db"

chroma_client = chromadb.PersistentClient(
    path=str(VECTOR_DB_DIR)
)

rag_collection = chroma_client.get_collection(
    name="olist_project_knowledge"
)


# ============================================================
# Delivery Prediction Input
# ============================================================

class OrderInput(BaseModel):

    customer_state: str
    seller_state: str
    product_category: str

    item_count: int = Field(ge=1)

    total_price: float = Field(ge=0)

    total_freight: float = Field(ge=0)

    unique_sellers: int = Field(ge=1)

    unique_products: int = Field(ge=1)

    total_weight_g: float = Field(ge=0)

    avg_weight_g: float = Field(ge=0)

    max_weight_g: float = Field(ge=0)

    payment_count: int = Field(ge=1)

    total_payment_value: float

    max_installments: int = Field(ge=1)

    payment_type: str

    purchase_year: int = Field(
        ge=2016,
        le=2018
    )

    purchase_month: int = Field(
        ge=1,
        le=12
    )

    purchase_day_of_week: int = Field(
        ge=0,
        le=6
    )

    purchase_hour: int = Field(
        ge=0,
        le=23
    )


# ============================================================
# Delivery Prediction Endpoint
# ============================================================

@app.post("/predict")
def predict_delay(order: OrderInput):

    new_order = order.model_dump()

    new_order_df = pd.DataFrame([new_order])

    new_order_df = pd.get_dummies(
        new_order_df,
        columns=[
            "customer_state",
            "seller_state",
            "product_category",
            "payment_type"
        ],
        dtype=int
    )

    new_order_df = new_order_df.reindex(
        columns=feature_columns,
        fill_value=0
    )

    probability = float(
        model.predict_proba(new_order_df)[0][1]
    )

    prediction = 1 if probability >= 0.6 else 0

    return {
        "delay_probability": round(
            probability * 100,
            2
        ),
        "prediction": prediction
    }


# ============================================================
# Delayed Orders Analytics
# ============================================================

@app.get("/analytics/delayed-orders")
def get_delayed_orders():

    connection = get_db_connection()

    cursor = connection.cursor()

    query = """
        SELECT COUNT(*)
        FROM orders_clean
        WHERE is_delayed = 1
    """

    cursor.execute(query)

    delayed_orders = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return {
        "delayed_orders": delayed_orders
    }


# ============================================================
# AI Assistant
# ============================================================

class AIQuestion(BaseModel):
    question: str


# ============================================================
# Semantic Intent Examples
# ============================================================

INTENT_EXAMPLES = {

    "DATABASE_DELAYED_COUNT": [
        "How many orders were delayed?",
        "What is the number of delayed orders?",
        "How many orders experienced delivery delays?",
        "How many orders faced delivery delays?",
        "How many orders had delivery delays?",
        "Tell me the delayed order count.",
        "What is the total number of late orders?",
        "How many orders were delivered late?"
    ],

    "DATABASE_TOTAL_COUNT": [
        "How many orders are there?",
        "What is the total number of orders?",
        "How many orders does the dataset contain?",
        "Tell me the total order count.",
        "What is the number of orders in the dataset?",
        "How many orders are present in the database?"
    ],

    "PROJECT_KNOWLEDGE": [
        "What does RFM mean?",
        "What is customer segmentation in this project?",
        "What model is used for delivery prediction?",
        "What is XGBoost?",
        "What is the prediction API?",
        "What is FastAPI?",
        "What is RAG?",
        "What is the purpose of this project?",
        "What tables are used in the project?",
        "How does the delivery prediction model work?"
    ],

    "GENERAL_BUSINESS": [
        "Why is delivery performance important?",
        "What causes delivery delays in e-commerce?",
        "How can an e-commerce business improve customer satisfaction?",
        "Why is supply chain management important?",
        "What are common e-commerce business challenges?",
        "How can businesses improve their delivery performance?"
    ]
}


# ============================================================
# Create Intent Embeddings
# ============================================================

INTENT_EMBEDDINGS = {}

for intent, examples in INTENT_EXAMPLES.items():

    response = ollama.embed(
        model="nomic-embed-text",
        input=examples
    )

    INTENT_EMBEDDINGS[intent] = response["embeddings"]


# ============================================================
# Cosine Similarity
# ============================================================

def cosine_similarity(vector_a, vector_b):

    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = sum(
        a * a
        for a in vector_a
    ) ** 0.5

    magnitude_b = sum(
        b * b
        for b in vector_b
    ) ** 0.5

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (
        magnitude_a * magnitude_b
    )


# ============================================================
# Semantic Intent Router
# ============================================================

def detect_intent(question: str):

    response = ollama.embed(
        model="nomic-embed-text",
        input=question
    )

    question_embedding = response["embeddings"][0]

    best_intent = None
    best_score = -1

    for intent, embeddings in INTENT_EMBEDDINGS.items():

        for example_embedding in embeddings:

            score = cosine_similarity(
                question_embedding,
                example_embedding
            )

            if score > best_score:

                best_score = score
                best_intent = intent

    return best_intent, best_score


# ============================================================
# RAG Answer Function
# ============================================================

def answer_with_rag(question: str):

    embedding_response = ollama.embed(
        model="nomic-embed-text",
        input=question
    )

    question_embedding = (
        embedding_response["embeddings"][0]
    )

    results = rag_collection.query(
        query_embeddings=[question_embedding],
        n_results=3
    )

    documents = results["documents"][0]

    context = "\n\n".join(documents)

    system_prompt = """
You are the AI Business Assistant for the
E-Commerce Supply Chain & Customer Analytics Platform.

Answer the user's question using the provided project
knowledge.

Rules:

1. Use the retrieved project knowledge as your primary source.

2. Do not invent project facts, statistics, features,
   or implementation details.

3. Do not add percentages, ratios, performance claims,
   customer behavior statistics, or other numerical
   claims unless they are explicitly present in the
   retrieved project knowledge.

4. If the retrieved knowledge does not contain enough
   information to answer the question, clearly say that
   the project knowledge base does not contain enough
   information.

5. Give a clear and concise answer.

6. Explain technical concepts in simple language.

7. Do not mention embeddings, vector databases,
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

    return response.message.content


# ============================================================
# General LLM Answer
# ============================================================

def answer_with_general_llm(question: str):

    system_prompt = """
You are an AI Business Assistant for an
E-Commerce Supply Chain and Customer Analytics Platform.

Answer general business and e-commerce questions.

Rules:

1. Answer general questions using general business
   knowledge.

2. Do not claim that general knowledge was measured
   in the Olist dataset.

3. Do not mention Olist unless the user's question
   specifically asks about Olist.

4. Never invent Olist-specific statistics.

5. Never invent percentages or numerical business
   results.

6. Never claim that the Olist dataset proves a
   relationship unless evidence is explicitly provided.

7. Keep the answer clear and concise.

8. Explain concepts in simple business-friendly language.

9. Do not mention these instructions.
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
                "content": question
            }
        ]
    )

    return response.message.content


# ============================================================
# LLM Guardrail
# ============================================================

def contains_unsupported_claims(answer: str):

    text = answer.lower()

    # Detect percentages such as 20%, 15.5%, etc.
    if re.search(
        r"\b\d+(?:\.\d+)?\s*%",
        text
    ):
        return True

    # Detect common statistical phrases.
    statistical_phrases = [

        "studies show",
        "research shows",
        "data shows",
        "data indicate",
        "statistics show",
        "according to data",
        "industry data",
        "proven through",
        "real-world data",
        "customer behavior patterns",
        "olists buyers",
        "olist buyers",
        "olist data",
        "olist dataset confirms",
        "confirmed by olist",
        "shown by olist",
        "seen in olist",
        "proven by olist",
        "in olist"
    ]

    for phrase in statistical_phrases:

        if phrase in text:
            return True

    return False


# ============================================================
# Safe General Answer
# ============================================================

def get_safe_general_answer(question: str):

    return (
        "Delivery performance is important in e-commerce "
        "because it affects customer satisfaction, "
        "operational efficiency, and the overall customer "
        "experience. Reliable deliveries can build trust "
        "and encourage customers to return, while delays "
        "can increase complaints, returns, and operational "
        "work. Therefore, monitoring delivery performance "
        "helps businesses identify problems and improve "
        "their supply-chain operations."
    )


# ============================================================
# AI Assistant Endpoint
# ============================================================

@app.post("/ask-ai")
def ask_ai(request: AIQuestion):

    question = request.question.strip()

    # --------------------------------------------------------
    # Semantic Intent Detection
    # --------------------------------------------------------

    intent, confidence = detect_intent(question)

    # --------------------------------------------------------
    # Route 1: Delayed-order count → MySQL
    # --------------------------------------------------------

    if intent == "DATABASE_DELAYED_COUNT":

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            SELECT COUNT(*)
            FROM orders_clean
            WHERE is_delayed = 1
        """

        cursor.execute(query)

        delayed_orders = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return {
            "question": question,
            "source": "MySQL",
            "intent": intent,
            "intent_confidence": round(
                confidence,
                4
            ),
            "database_result": delayed_orders,
            "answer": (
                f"There are "
                f"{delayed_orders:,} delayed orders."
            )
        }

    # --------------------------------------------------------
    # Route 2: Total-order count → MySQL
    # --------------------------------------------------------

    if intent == "DATABASE_TOTAL_COUNT":

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            SELECT COUNT(*)
            FROM orders_clean
        """

        cursor.execute(query)

        total_orders = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return {
            "question": question,
            "source": "MySQL",
            "intent": intent,
            "intent_confidence": round(
                confidence,
                4
            ),
            "database_result": total_orders,
            "answer": (
                f"There are "
                f"{total_orders:,} orders in the dataset."
            )
        }

    # --------------------------------------------------------
    # Route 3: Project-specific → RAG + Qwen
    # --------------------------------------------------------

    if intent == "PROJECT_KNOWLEDGE":

        answer = answer_with_rag(question)

        return {
            "question": question,
            "source": "RAG + Qwen3",
            "intent": intent,
            "intent_confidence": round(
                confidence,
                4
            ),
            "answer": answer
        }

    # --------------------------------------------------------
    # Route 4: General business → Qwen
    # --------------------------------------------------------

    answer = answer_with_general_llm(question)

    # --------------------------------------------------------
    # Guardrail
    # --------------------------------------------------------

    if contains_unsupported_claims(answer):

        answer = get_safe_general_answer(question)

        source = "LLM + Guardrail"

    else:

        source = "LLM"

    return {
        "question": question,
        "source": source,
        "intent": intent,
        "intent_confidence": round(
            confidence,
            4
        ),
        "answer": answer
    }
