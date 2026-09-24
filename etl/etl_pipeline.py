import pandas as pd
import mysql.connector


# ============================================================
# 1. EXTRACT
# ============================================================

orders = pd.read_csv("data/olist_orders_dataset.csv")

print("Data extracted successfully!")


# ============================================================
# 2. TRANSFORM — Convert date columns
# ============================================================

orders["order_purchase_timestamp"] = pd.to_datetime(
    orders["order_purchase_timestamp"]
)

orders["order_approved_at"] = pd.to_datetime(
    orders["order_approved_at"]
)

orders["order_delivered_carrier_date"] = pd.to_datetime(
    orders["order_delivered_carrier_date"]
)

orders["order_delivered_customer_date"] = pd.to_datetime(
    orders["order_delivered_customer_date"]
)

orders["order_estimated_delivery_date"] = pd.to_datetime(
    orders["order_estimated_delivery_date"]
)

print("Date columns transformed successfully!")


# ============================================================
# 3. CREATE DELIVERY FEATURES
# ============================================================

# Number of days from purchase to delivery
orders["delivery_days"] = (
    orders["order_delivered_customer_date"]
    - orders["order_purchase_timestamp"]
).dt.days


# Difference between actual and estimated delivery
# Positive value = delivered late
orders["delivery_delay_days"] = (
    orders["order_delivered_customer_date"]
    - orders["order_estimated_delivery_date"]
).dt.days


# 1 = delayed
# 0 = not delayed
orders["is_delayed"] = (
    orders["delivery_delay_days"] > 0
).astype(int)


# Number of days from approval to carrier handover
orders["processing_days"] = (
    orders["order_delivered_carrier_date"]
    - orders["order_approved_at"]
).dt.days


# Negative processing time is invalid
# Convert it to missing value
orders.loc[
    orders["processing_days"] < 0,
    "processing_days"
] = None

print("Delivery features created successfully!")


# ============================================================
# 4. MYSQL CONNECTION
# ============================================================

conn = mysql.connector.connect(
    host="127.0.0.1",
    port=3307,
    user="root",
    password="kAyp@2323",
    database="olist_db"
)

print("MySQL connected successfully!")


# ============================================================
# 5. CREATE CURSOR
# ============================================================

cursor = conn.cursor()

print("Ready to load data into MySQL!")


# ============================================================
# 6. CREATE CLEAN ORDERS TABLE
# ============================================================

cursor.execute("DROP TABLE IF EXISTS orders_clean")

cursor.execute("""
CREATE TABLE orders_clean (
    order_id VARCHAR(50),
    customer_id VARCHAR(50),
    order_status VARCHAR(30),
    order_purchase_timestamp DATETIME,
    order_approved_at DATETIME,
    order_delivered_carrier_date DATETIME,
    order_delivered_customer_date DATETIME,
    order_estimated_delivery_date DATETIME,
    delivery_days INT,
    delivery_delay_days INT,
    is_delayed INT,
    processing_days INT
)
""")

conn.commit()

print("orders_clean table created!")


# ============================================================
# 7. PREPARE DATA FOR MYSQL
# ============================================================

load_columns = [
    "order_id",
    "customer_id",
    "order_status",
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "delivery_days",
    "delivery_delay_days",
    "is_delayed",
    "processing_days"
]

data = orders[load_columns].copy()


# Convert Pandas NaN / NaT to Python None
# MySQL will store None as NULL
data = data.astype(object).where(pd.notna(data), None)

data = data.values.tolist()


# ============================================================
# 8. INSERT DATA INTO MYSQL
# ============================================================

insert_query = """
INSERT INTO orders_clean (
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    delivery_days,
    delivery_delay_days,
    is_delayed,
    processing_days
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

cursor.executemany(insert_query, data)

conn.commit()

print("Orders loaded successfully!")

# ============================================================
# 10. LOAD CUSTOMERS
# ============================================================

customers = pd.read_csv("data/olist_customers_dataset.csv")

cursor.execute("DROP TABLE IF EXISTS customers_clean")

cursor.execute("""
CREATE TABLE customers_clean (
    customer_id VARCHAR(50),
    customer_unique_id VARCHAR(50),
    customer_zip_code_prefix INT,
    customer_city VARCHAR(100),
    customer_state VARCHAR(10)
)
""")

customer_columns = [
    "customer_id",
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state"
]

customer_data = customers[customer_columns].copy()

customer_data = customer_data.astype(object).where(
    pd.notna(customer_data),
    None
)

customer_data = customer_data.values.tolist()

customer_insert = """
INSERT INTO customers_clean (
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
)
VALUES (%s, %s, %s, %s, %s)
"""

cursor.executemany(customer_insert, customer_data)

conn.commit()

print("Customers loaded successfully!")

# ============================================================
# 11. LOAD ORDER ITEMS
# ============================================================

order_items = pd.read_csv(
    "data/olist_order_items_dataset.csv"
)

cursor.execute("DROP TABLE IF EXISTS order_items_clean")

cursor.execute("""
CREATE TABLE order_items_clean (
    order_id VARCHAR(50),
    order_item_id INT,
    product_id VARCHAR(50),
    seller_id VARCHAR(50),
    shipping_limit_date DATETIME,
    price DECIMAL(10,2),
    freight_value DECIMAL(10,2)
)
""")

# Convert shipping date
order_items["shipping_limit_date"] = pd.to_datetime(
    order_items["shipping_limit_date"]
)

order_item_columns = [
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "shipping_limit_date",
    "price",
    "freight_value"
]

order_item_data = order_items[order_item_columns].copy()

# Convert NaN / NaT to None
order_item_data = order_item_data.astype(object).where(
    pd.notna(order_item_data),
    None
)

order_item_data = order_item_data.values.tolist()

order_item_insert = """
INSERT INTO order_items_clean (
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date,
    price,
    freight_value
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

cursor.executemany(
    order_item_insert,
    order_item_data
)

conn.commit()

print("Order items loaded successfully!")

# ============================================================
# 12. LOAD PRODUCTS
# ============================================================

products = pd.read_csv(
    "data/olist_products_dataset.csv"
)

cursor.execute("DROP TABLE IF EXISTS products_clean")

cursor.execute("""
CREATE TABLE products_clean (
    product_id VARCHAR(50),
    product_category_name VARCHAR(100),
    product_name_lenght INT,
    product_description_lenght INT,
    product_photos_qty INT,
    product_weight_g INT,
    product_length_cm INT,
    product_height_cm INT,
    product_width_cm INT
)
""")

product_columns = [
    "product_id",
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm"
]

product_data = products[product_columns].copy()

# Convert NaN to None
product_data = product_data.astype(object).where(
    pd.notna(product_data),
    None
)

product_data = product_data.values.tolist()

product_insert = """
INSERT INTO products_clean (
    product_id,
    product_category_name,
    product_name_lenght,
    product_description_lenght,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

cursor.executemany(
    product_insert,
    product_data
)

conn.commit()

print("Products loaded successfully!")

# ============================================================
# 13. LOAD PAYMENTS
# ============================================================

payments = pd.read_csv(
    "data/olist_order_payments_dataset.csv"
)

cursor.execute("DROP TABLE IF EXISTS payments_clean")

cursor.execute("""
CREATE TABLE payments_clean (
    order_id VARCHAR(50),
    payment_sequential INT,
    payment_type VARCHAR(30),
    payment_installments INT,
    payment_value DECIMAL(10,2)
)
""")

payment_columns = [
    "order_id",
    "payment_sequential",
    "payment_type",
    "payment_installments",
    "payment_value"
]

payment_data = payments[payment_columns].copy()

# Convert NaN to None
payment_data = payment_data.astype(object).where(
    pd.notna(payment_data),
    None
)

payment_data = payment_data.values.tolist()

payment_insert = """
INSERT INTO payments_clean (
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value
)
VALUES (%s, %s, %s, %s, %s)
"""

cursor.executemany(
    payment_insert,
    payment_data
)

conn.commit()

print("Payments loaded successfully!")

# ============================================================
# 14. LOAD REVIEWS
# ============================================================

reviews = pd.read_csv(
    "data/olist_order_reviews_dataset.csv"
)

cursor.execute("DROP TABLE IF EXISTS reviews_clean")

cursor.execute("""
CREATE TABLE reviews_clean (
    review_id VARCHAR(50),
    order_id VARCHAR(50),
    review_score INT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date DATETIME,
    review_answer_timestamp DATETIME
)
""")

# Convert date columns
reviews["review_creation_date"] = pd.to_datetime(
    reviews["review_creation_date"]
)

reviews["review_answer_timestamp"] = pd.to_datetime(
    reviews["review_answer_timestamp"]
)

review_columns = [
    "review_id",
    "order_id",
    "review_score",
    "review_comment_title",
    "review_comment_message",
    "review_creation_date",
    "review_answer_timestamp"
]

review_data = reviews[review_columns].copy()

# Convert NaN / NaT to None
review_data = review_data.astype(object).where(
    pd.notna(review_data),
    None
)

review_data = review_data.values.tolist()

review_insert = """
INSERT INTO reviews_clean (
    review_id,
    order_id,
    review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date,
    review_answer_timestamp
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

cursor.executemany(
    review_insert,
    review_data
)

conn.commit()

print("Reviews loaded successfully!")

# ============================================================
# 15. LOAD SELLERS
# ============================================================

sellers = pd.read_csv(
    "data/olist_sellers_dataset.csv"
)

cursor.execute("DROP TABLE IF EXISTS sellers_clean")

cursor.execute("""
CREATE TABLE sellers_clean (
    seller_id VARCHAR(50),
    seller_zip_code_prefix INT,
    seller_city VARCHAR(100),
    seller_state VARCHAR(10)
)
""")

seller_columns = [
    "seller_id",
    "seller_zip_code_prefix",
    "seller_city",
    "seller_state"
]

seller_data = sellers[seller_columns].copy()

# Convert NaN to None
seller_data = seller_data.astype(object).where(
    pd.notna(seller_data),
    None
)

seller_data = seller_data.values.tolist()

seller_insert = """
INSERT INTO sellers_clean (
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
)
VALUES (%s, %s, %s, %s)
"""

cursor.executemany(
    seller_insert,
    seller_data
)

conn.commit()

print("Sellers loaded successfully!")

# ============================================================
# 16. LOAD CATEGORY TRANSLATION
# ============================================================

category_translation = pd.read_csv(
    "data/product_category_name_translation.csv"
)

cursor.execute(
    "DROP TABLE IF EXISTS category_translation_clean"
)

cursor.execute("""
CREATE TABLE category_translation_clean (
    product_category_name VARCHAR(100),
    product_category_name_english VARCHAR(100)
)
""")

category_columns = [
    "product_category_name",
    "product_category_name_english"
]

category_data = category_translation[category_columns].copy()

# Convert NaN to None
category_data = category_data.astype(object).where(
    pd.notna(category_data),
    None
)

category_data = category_data.values.tolist()

category_insert = """
INSERT INTO category_translation_clean (
    product_category_name,
    product_category_name_english
)
VALUES (%s, %s)
"""

cursor.executemany(
    category_insert,
    category_data
)

conn.commit()

print("Category translation loaded successfully!")


# ============================================================
#  CLOSE CONNECTION
# ============================================================

cursor.close()
conn.close()

print("ETL completed successfully!")