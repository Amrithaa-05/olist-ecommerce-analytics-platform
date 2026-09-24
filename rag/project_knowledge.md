# E-Commerce Supply Chain & Customer Analytics Platform

## 1. Project Overview

This project is an E-Commerce Supply Chain and Customer Analytics Platform built using the Brazilian Olist e-commerce dataset.

The platform combines:

- Python ETL and data validation
- MySQL
- SQL analytics
- RFM customer segmentation
- XGBoost machine learning
- Power BI
- FastAPI
- Streamlit
- Local LLM using Ollama and Qwen3 4B
- Retrieval-Augmented Generation (RAG)

The purpose of the platform is to analyze e-commerce sales, customers, payments, products, sellers, reviews, and delivery performance while providing machine-learning-based delivery-delay prediction and an AI business assistant.


## 2. Data Processing

The raw Olist CSV files are processed using a Python ETL pipeline.

The ETL pipeline performs:

- Data extraction
- Data cleaning
- Date transformation
- Delivery feature engineering
- Data validation
- Loading cleaned data into MySQL

The cleaned data is stored in the MySQL database named `olist_db`.


## 3. Main MySQL Tables

### orders_clean

Contains information about customer orders.

Important information includes:

- order_id
- customer_id
- order_status
- order_purchase_timestamp
- order_approved_at
- order_delivered_carrier_date
- order_delivered_customer_date
- order_estimated_delivery_date
- delivery_days
- delivery_delay_days
- is_delayed

The `is_delayed` field is used to identify whether an order was delivered later than the expected delivery date.


### customers_clean

Contains customer information.

Important fields include:

- customer_id
- customer_unique_id
- customer_zip_code_prefix
- customer_city
- customer_state

`customer_unique_id` represents the unique customer across orders.


### order_items_clean

Contains item-level information for orders.

Important fields include:

- order_id
- order_item_id
- product_id
- seller_id
- price
- freight_value


### products_clean

Contains product information.

Important fields include:

- product_id
- product_category_name
- product_weight_g
- product_length_cm
- product_height_cm
- product_width_cm


### payments_clean

Contains payment information.

Important fields include:

- order_id
- payment_type
- payment_installments
- payment_value

An order can have multiple payment records.


### sellers_clean

Contains seller information.

Important fields include:

- seller_id
- seller_zip_code_prefix
- seller_city
- seller_state


### reviews_clean

Contains customer review information.

Important fields include:

- review_id
- order_id
- review_score
- review_comment_title
- review_comment_message


### category_translation_clean

Contains product category translations used for analysis and visualization.


## 4. Delivery Analytics

Delivery performance is one of the major analytical areas of the project.

Delivery delay is represented using the `is_delayed` field.

An order is considered delayed when its actual customer delivery date is later than its estimated delivery date.

The platform calculates delivery-related features such as:

- delivery_days
- delivery_delay_days
- is_delayed

The dataset contains 99,441 orders.

There are 6,535 delayed orders in the cleaned orders table.


## 5. Customer Segmentation

The project uses RFM analysis for customer segmentation.

RFM means:

- Recency: how recently a customer purchased
- Frequency: how often the customer purchased
- Monetary: how much the customer spent

The RFM analysis uses `customer_unique_id`.

The analysis is based on delivered orders.

The reference date used for the RFM calculation is 2018-10-17.


## 6. Customer Segments

The project creates a `customer_segmentation` view.

The segments are:

### Champions

Customers with strong recency, frequency, and monetary scores.


### Loyal Customers

Customers who purchase relatively frequently and have good recency.


### New Customers

Customers with recent activity and a frequency of one order.


### At Risk

Customers with low recency and multiple purchases.


### High-Value At Risk

Customers with low recency, one purchase, and relatively high monetary value.


### Lost / Inactive

Customers with low recency, one purchase, and relatively low monetary value.


### Regular Customers

Customers who do not fall into the other defined segments.


## 7. RFM Segment Distribution

The current segmentation produced approximately:

- Lost / Inactive: 38,586
- New Customers: 26,488
- Regular Customers: 19,939
- High-Value At Risk: 6,194
- At Risk: 1,243
- Loyal Customers: 890
- Champions: 17


## 8. Delivery Delay Prediction Model

The project uses XGBoost to predict whether an order is likely to experience a delivery delay.

The model uses order, customer, seller, product, payment, and purchase-time features.

Categorical features are encoded using one-hot encoding.

The model was trained using a stratified train-test split.


## 9. Machine Learning Features

Important model features include:

- customer_state
- seller_state
- product_category
- item_count
- total_price
- total_freight
- unique_sellers
- unique_products
- total_weight_g
- avg_weight_g
- max_weight_g
- payment_count
- total_payment_value
- max_installments
- payment_type
- purchase_year
- purchase_month
- purchase_day_of_week
- purchase_hour


## 10. Model Evaluation

The final model uses a prediction threshold of 0.6.

The recorded evaluation results are:

- Accuracy: approximately 0.8493
- ROC-AUC: approximately 0.7584

Because delayed orders are much less common than non-delayed orders, accuracy alone is not sufficient for evaluating the model.

Precision, recall, F1-score, ROC-AUC, and threshold analysis were considered when evaluating the model.


## 11. Prediction API

FastAPI provides an API endpoint for delivery-delay prediction.

Endpoint:

POST `/predict`

The endpoint accepts order information and returns:

- delay_probability
- prediction

The prediction value is:

- 0 = predicted not delayed
- 1 = predicted delayed

The production prediction threshold is 0.6.


## 12. Analytics API

FastAPI also provides database-backed analytics endpoints.

One endpoint is:

GET `/analytics/delayed-orders`

This endpoint queries MySQL and returns the number of delayed orders.

The API does not ask the language model to calculate the number.


## 13. AI Business Assistant

The platform contains an AI Business Assistant built using:

- Streamlit
- FastAPI
- MySQL
- Ollama
- Qwen3 4B

The assistant is designed to answer questions about the e-commerce analytics platform and provide business-oriented explanations.


## 14. AI Question Routing

The assistant uses different sources depending on the type of question.

Exact numerical questions should be answered using MySQL.

General business and conceptual questions can be answered using the language model.

Project-specific knowledge can be answered using the RAG knowledge base.


## 15. Database-Grounded Questions

For questions requiring exact numerical information, the application should retrieve the result directly from MySQL.

For example:

Question:

"How many orders are there?"

Source:

MySQL

Result:

99,441 orders.


Question:

"How many orders were delayed?"

Source:

MySQL

Result:

6,535 delayed orders.

The language model should not invent or guess these values.


## 16. RAG

Retrieval-Augmented Generation is used to provide the language model with project-specific knowledge.

The purpose of RAG is to allow the AI assistant to retrieve relevant information from the project's knowledge base before generating an answer.

The vector database should contain useful textual knowledge rather than every raw numerical order record.

Potential RAG content includes:

- Project documentation
- Table descriptions
- KPI definitions
- RFM definitions
- Customer segment explanations
- Machine learning model information
- API documentation
- Business terminology
- Selected textual product or review information


## 17. RAG and MySQL Responsibilities

MySQL is responsible for exact structured data.

Examples:

- Number of orders
- Number of delayed orders
- Revenue
- Average delivery time
- Customer counts
- Segment counts

RAG is responsible for semantic and textual knowledge.

Examples:

- What does RFM mean?
- What does an At Risk customer mean?
- What does the delivery prediction model do?
- What does the `is_delayed` field represent?


## 18. AI Assistant Architecture

The intended architecture is:

User Question
↓
Streamlit
↓
FastAPI
↓
Question Routing
↓
├── Structured numerical question → MySQL
│
├── Project knowledge question → RAG
│
└── General business question → Qwen3
↓
Final Business Answer


## 19. Power BI Dashboard

Power BI is used to visualize the cleaned data and analytical results.

The dashboard contains four main pages:

### Page 1

Overview and KPIs


### Page 2

Sales, Customer and Delivery Insights


### Page 3

Customer and Payment Analytics


### Page 4

Geographic and Product Performance


## 20. Technology Stack

### Data Engineering

- Python
- Pandas
- MySQL


### Data Analytics

- SQL
- RFM analysis
- Power BI


### Machine Learning

- XGBoost
- One-hot encoding
- Classification


### Backend

- FastAPI
- Pydantic


### Frontend

- Streamlit


### Generative AI

- Ollama
- Qwen3 4B
- RAG
- Vector database
- Embeddings


## 21. Project Goal

The overall goal is to create an interactive analytics platform that combines structured data analytics, machine learning, and generative AI.

The AI assistant should not simply generate generic chatbot responses.

It should use the appropriate source for each question:

- MySQL for exact numerical facts
- RAG for project-specific knowledge
- Qwen for general business reasoning and natural-language explanations

This separation improves reliability and reduces the chance of hallucinated numerical results.