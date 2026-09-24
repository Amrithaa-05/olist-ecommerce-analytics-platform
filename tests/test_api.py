from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_total_orders():
    response = client.post(
        "/ask-ai",
        json={
            "question": "How many orders are there in total?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "DATABASE_TOTAL_COUNT"
    assert data["source"] == "MySQL"
    assert data["database_result"] == 99441


def test_delayed_orders():
    response = client.post(
        "/ask-ai",
        json={
            "question": "How many orders had a delivery delay?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "DATABASE_DELAYED_COUNT"
    assert data["source"] == "MySQL"
    assert data["database_result"] == 6535


def test_general_business_question():
    response = client.post(
        "/ask-ai",
        json={
            "question": "What are some ways an e-commerce company can reduce delivery delays?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "GENERAL_BUSINESS"
    assert data["source"] == "LLM"


def test_invalid_prediction():
    response = client.post(
        "/predict",
        json={
            "customer_state": "SP",
            "seller_state": "SP",
            "product_category": "health_beauty",
            "item_count": 0,
            "total_price": 100,
            "total_freight": 20,
            "unique_sellers": 1,
            "unique_products": 1,
            "total_weight_g": 500,
            "avg_weight_g": 500,
            "max_weight_g": 500,
            "payment_type": "credit_card",
            "payment_count": 1,
            "max_installments": 1,
            "purchase_year": 2018,
            "month": 8,
            "day_of_week": 3,
            "hour": 14
        }
    )

    assert response.status_code == 422