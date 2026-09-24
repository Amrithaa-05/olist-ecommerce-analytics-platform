import os
from pathlib import Path
from datetime import date

import mysql.connector
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="E-Commerce Analytics Platform",
    page_icon="📊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

FASTAPI_URL = "http://127.0.0.1:8000"


# --------------------------------------------------
# STATE MAPPING
# --------------------------------------------------

state_name_mapping = {
    "SP": "Sao Paulo",
    "RJ": "Rio de Janeiro",
    "MG": "Minas Gerais",
    "BA": "Bahia",
    "PR": "Parana",
    "SC": "Santa Catarina",
    "RS": "Rio Grande do Sul",
    "PE": "Pernambuco",
    "CE": "Ceara",
    "PA": "Para",
    "GO": "Goias",
    "ES": "Espirito Santo",
    "MA": "Maranhao",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "AL": "Alagoas",
    "PI": "Piaui",
    "PB": "Paraiba",
    "RN": "Rio Grande do Norte",
    "SE": "Sergipe",
    "AM": "Amazonas",
    "RO": "Rondonia",
    "TO": "Tocantins",
    "AC": "Acre",
    "AP": "Amapa",
    "RR": "Roraima",
    "DF": "Federal District"
}


# --------------------------------------------------
# MYSQL CONNECTION
# --------------------------------------------------

def get_connection():

    password = os.getenv("MYSQL_PASSWORD")

    if not password:
        raise ValueError(
            "MYSQL_PASSWORD is not configured in .env"
        )

    return mysql.connector.connect(
        host="127.0.0.1",
        port=3307,
        user="root",
        password=password,
        database="olist_db"
    )


# --------------------------------------------------
# ANALYTICS QUERIES
# --------------------------------------------------

@st.cache_data(ttl=60)
def load_analytics(start_date, end_date):

    query = """
    SELECT
        (
            SELECT COUNT(*)
            FROM orders_clean
            WHERE DATE(order_purchase_timestamp)
                  BETWEEN %s AND %s
        ) AS total_orders,

        (
            SELECT COALESCE(SUM(p.payment_value), 0)
            FROM payments_clean p
            INNER JOIN orders_clean o
                ON p.order_id = o.order_id
            WHERE DATE(o.order_purchase_timestamp)
                  BETWEEN %s AND %s
        ) AS total_revenue,

        (
            SELECT COUNT(DISTINCT c.customer_unique_id)
            FROM customers_clean c
            INNER JOIN orders_clean o
                ON c.customer_id = o.customer_id
            WHERE DATE(o.order_purchase_timestamp)
                  BETWEEN %s AND %s
        ) AS total_customers,

        (
            SELECT COALESCE(AVG(o.delivery_days), 0)
            FROM orders_clean o
            WHERE DATE(o.order_purchase_timestamp)
                  BETWEEN %s AND %s
              AND o.delivery_days IS NOT NULL
        ) AS avg_delivery_days,

        (
            SELECT COALESCE(AVG(o.is_delayed) * 100, 0)
            FROM orders_clean o
            WHERE DATE(o.order_purchase_timestamp)
                  BETWEEN %s AND %s
              AND o.is_delayed IS NOT NULL
        ) AS delayed_percentage
    """

    params = (
        start_date,
        end_date,
        start_date,
        end_date,
        start_date,
        end_date,
        start_date,
        end_date,
        start_date,
        end_date
    )

    connection = get_connection()

    try:
        df = pd.read_sql(
            query,
            connection,
            params=params
        )

        return df.iloc[0]

    finally:
        connection.close()


@st.cache_data(ttl=60)
def load_orders_over_time(start_date, end_date):

    query = """
    SELECT
        DATE_FORMAT(order_purchase_timestamp, '%Y-%m') AS month,
        COUNT(*) AS orders
    FROM orders_clean
    WHERE DATE(order_purchase_timestamp)
          BETWEEN %s AND %s
    GROUP BY DATE_FORMAT(order_purchase_timestamp, '%Y-%m')
    ORDER BY month
    """

    connection = get_connection()

    try:
        return pd.read_sql(
            query,
            connection,
            params=(start_date, end_date)
        )

    finally:
        connection.close()


@st.cache_data(ttl=60)
def load_revenue_by_category(start_date, end_date):

    query = """
    SELECT
        COALESCE(p.product_category_name, 'Unknown') AS category,
        SUM(oi.price + oi.freight_value) AS revenue
    FROM order_items_clean oi
    LEFT JOIN products_clean p
        ON oi.product_id = p.product_id
    INNER JOIN orders_clean o
        ON oi.order_id = o.order_id
    WHERE DATE(o.order_purchase_timestamp)
          BETWEEN %s AND %s
    GROUP BY p.product_category_name
    ORDER BY revenue DESC
    LIMIT 15
    """

    connection = get_connection()

    try:
        return pd.read_sql(
            query,
            connection,
            params=(start_date, end_date)
        )

    finally:
        connection.close()


@st.cache_data(ttl=60)
def load_orders_by_state(start_date, end_date):

    query = """
    SELECT
        c.customer_state AS state,
        COUNT(DISTINCT o.order_id) AS orders
    FROM orders_clean o
    INNER JOIN customers_clean c
        ON o.customer_id = c.customer_id
    WHERE DATE(o.order_purchase_timestamp)
          BETWEEN %s AND %s
    GROUP BY c.customer_state
    ORDER BY orders DESC
    """

    connection = get_connection()

    try:
        return pd.read_sql(
            query,
            connection,
            params=(start_date, end_date)
        )

    finally:
        connection.close()


@st.cache_data(ttl=60)
def load_delivery_performance(start_date, end_date):

    query = """
    SELECT
        CASE
            WHEN is_delayed = 1 THEN 'Delayed'
            WHEN is_delayed = 0 THEN 'On Time'
        END AS delivery_status,
        COUNT(*) AS orders
    FROM orders_clean
    WHERE DATE(order_purchase_timestamp)
          BETWEEN %s AND %s
      AND is_delayed IS NOT NULL
    GROUP BY is_delayed
    ORDER BY is_delayed
    """

    connection = get_connection()

    try:
        return pd.read_sql(
            query,
            connection,
            params=(start_date, end_date)
        )

    finally:
        connection.close()


@st.cache_data(ttl=60)
def load_average_delivery_by_state(start_date, end_date):

    query = """
    SELECT
        c.customer_state AS state,
        AVG(o.delivery_days) AS avg_delivery_days
    FROM orders_clean o
    INNER JOIN customers_clean c
        ON o.customer_id = c.customer_id
    WHERE DATE(o.order_purchase_timestamp)
          BETWEEN %s AND %s
      AND o.delivery_days IS NOT NULL
    GROUP BY c.customer_state
    ORDER BY avg_delivery_days DESC
    """

    connection = get_connection()

    try:
        return pd.read_sql(
            query,
            connection,
            params=(start_date, end_date)
        )

    finally:
        connection.close()


@st.cache_data(ttl=60)
def load_customer_segments():

    query = """
    SELECT
        customer_segment,
        COUNT(*) AS customers
    FROM customer_segmentation
    GROUP BY customer_segment
    ORDER BY customers DESC
    """

    connection = get_connection()

    try:
        return pd.read_sql(
            query,
            connection
        )

    finally:
        connection.close()


# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.title("📊 E-Commerce Analytics")

page = st.sidebar.radio(
    "Select Page",
    [
        "📊 Analytics",
        "🚚 Delivery Prediction",
        "🤖 AI Assistant"
    ]
)


# ==================================================
# ANALYTICS PAGE
# ==================================================

if page == "📊 Analytics":

    st.title("📊 E-Commerce Analytics Dashboard")

    # --------------------------------------------------
    # DATE FILTER
    # --------------------------------------------------

    st.subheader("📅 Select Date Range")

    date_col1, date_col2 = st.columns(2)

    with date_col1:

        start_date = st.date_input(
            "Start Date",
            value=date(2016, 9, 4),
            min_value=date(2016, 9, 4),
            max_value=date(2018, 10, 17)
        )

    with date_col2:

        end_date = st.date_input(
            "End Date",
            value=date(2018, 10, 17),
            min_value=date(2016, 9, 4),
            max_value=date(2018, 10, 17)
        )

    if start_date > end_date:

        st.error(
            "Start Date cannot be later than End Date."
        )

        st.stop()

    try:

        analytics = load_analytics(
            start_date,
            end_date
        )

        # --------------------------------------------------
        # KPI CARDS
        # --------------------------------------------------

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "Total Orders",
            f"{int(analytics['total_orders']):,}"
        )

        col2.metric(
            "Total Revenue",
            f"₹{analytics['total_revenue']:,.2f}"
        )

        col3.metric(
            "Customers",
            f"{int(analytics['total_customers']):,}"
        )

        col4.metric(
            "Avg Delivery Days",
            f"{analytics['avg_delivery_days']:.2f}"
        )

        col5.metric(
            "Delayed Orders",
            f"{analytics['delayed_percentage']:.2f}%"
        )

        st.success(
            f"Analytics loaded for "
            f"{start_date.strftime('%d %b %Y')} "
            f"to "
            f"{end_date.strftime('%d %b %Y')}."
        )

        # --------------------------------------------------
        # ORDERS OVER TIME
        # --------------------------------------------------

        st.subheader("📈 Orders Over Time")

        orders_df = load_orders_over_time(
            start_date,
            end_date
        )

        if not orders_df.empty:

            orders_df["month"] = pd.to_datetime(
                orders_df["month"]
            )

            orders_df = orders_df.set_index(
                "month"
            )

            st.line_chart(
                orders_df,
                y="orders",
                use_container_width=True
            )

        # --------------------------------------------------
        # REVENUE BY PRODUCT CATEGORY
        # --------------------------------------------------

        st.subheader("📊 Revenue by Product Category")

        revenue_df = load_revenue_by_category(
            start_date,
            end_date
        )

        if not revenue_df.empty:

            revenue_df = revenue_df.set_index(
                "category"
            )

            st.bar_chart(
                revenue_df,
                y="revenue",
                use_container_width=True
            )

        # --------------------------------------------------
        # ORDERS BY CUSTOMER STATE
        # --------------------------------------------------

        st.subheader("📍 Orders by Customer State")

        state_df = load_orders_by_state(
            start_date,
            end_date
        )

        if not state_df.empty:

            state_df["state"] = state_df["state"].map(
                state_name_mapping
            ).fillna(
                state_df["state"]
            )

            state_df = state_df.set_index(
                "state"
            )

            st.bar_chart(
                state_df,
                y="orders",
                use_container_width=True
            )

        # --------------------------------------------------
        # DELIVERY PERFORMANCE
        # --------------------------------------------------

        st.subheader("🚚 Delivery Performance")

        delivery_df = load_delivery_performance(
            start_date,
            end_date
        )

        if not delivery_df.empty:

            delivery_df = delivery_df.set_index(
                "delivery_status"
            )

            st.bar_chart(
                delivery_df,
                y="orders",
                use_container_width=True
            )

        # --------------------------------------------------
        # AVERAGE DELIVERY TIME BY STATE
        # --------------------------------------------------

        st.subheader("⏱️ Average Delivery Time by State")

        avg_delivery_df = load_average_delivery_by_state(
            start_date,
            end_date
        )

        if not avg_delivery_df.empty:

            avg_delivery_df["state"] = avg_delivery_df[
                "state"
            ].map(
                state_name_mapping
            ).fillna(
                avg_delivery_df["state"]
            )

            avg_delivery_df = avg_delivery_df.set_index(
                "state"
            )

            st.bar_chart(
                avg_delivery_df,
                y="avg_delivery_days",
                use_container_width=True
            )

        # --------------------------------------------------
        # CUSTOMER SEGMENTS
        # --------------------------------------------------

        st.subheader("👥 Customer Segments")

        st.caption(
            "Customer segmentation is based on the full customer history."
        )

        segments_df = load_customer_segments()

        if not segments_df.empty:

            segments_df = segments_df.set_index(
                "customer_segment"
            )

            st.bar_chart(
                segments_df,
                y="customers",
                use_container_width=True
            )

    except Exception as e:

        st.error(
            f"Unable to load analytics: {e}"
        )


# ==================================================
# DELIVERY PREDICTION PAGE
# ==================================================

elif page == "🚚 Delivery Prediction":

    st.title("🚚 Delivery Delay Prediction")

    st.write(
        "Enter order details to predict the probability of delivery delay."
    )

    with st.form("prediction_form"):

        # --------------------------------------------------
        # ORDER DETAILS
        # --------------------------------------------------

        st.subheader("🛒 Order Details")

        col1, col2 = st.columns(2)

        with col1:

            customer_state_name = st.selectbox(
                "Customer State",
                list(state_name_mapping.values())
            )

            seller_state_name = st.selectbox(
                "Seller State",
                list(state_name_mapping.values())
            )

            product_category = st.text_input(
                "Product Category",
                value="health_beauty"
            )

            item_count = st.number_input(
                "Item Count",
                min_value=1,
                value=1
            )

        with col2:

            total_price = st.number_input(
                "Total Price",
                min_value=0.0,
                value=100.0
            )

            total_freight = st.number_input(
                "Total Freight",
                min_value=0.0,
                value=20.0
            )

            unique_sellers = st.number_input(
                "Unique Sellers",
                min_value=1,
                value=1
            )

            unique_products = st.number_input(
                "Unique Products",
                min_value=1,
                value=1
            )

        # --------------------------------------------------
        # PRODUCT & SHIPPING DETAILS
        # --------------------------------------------------

        st.subheader("📦 Product & Shipping Details")

        col1, col2, col3 = st.columns(3)

        with col1:

            total_weight_g = st.number_input(
                "Total Weight (g)",
                min_value=0.0,
                value=500.0
            )

        with col2:

            avg_weight_g = st.number_input(
                "Average Weight (g)",
                min_value=0.0,
                value=500.0
            )

        with col3:

            max_weight_g = st.number_input(
                "Maximum Weight (g)",
                min_value=0.0,
                value=500.0
            )

        # --------------------------------------------------
        # PAYMENT DETAILS
        # --------------------------------------------------

        st.subheader("💳 Payment Details")

        col1, col2, col3 = st.columns(3)

        with col1:

            payment_count = st.number_input(
                "Payment Count",
                min_value=1,
                value=1
            )

        with col2:

            total_payment_value = st.number_input(
                "Total Payment Value",
                min_value=0.0,
                value=120.0
            )

        with col3:

            max_installments = st.number_input(
                "Maximum Installments",
                min_value=1,
                value=1
            )

        payment_type = st.selectbox(
            "Payment Type",
            [
                "credit_card",
                "boleto",
                "voucher",
                "debit_card"
            ]
        )

        # --------------------------------------------------
        # PURCHASE DETAILS
        # --------------------------------------------------

        st.subheader("🕐 Purchase Details")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            purchase_year = st.number_input(
                "Purchase Year",
                min_value=2016,
                max_value=2018,
                value=2018
            )

        with col2:

            purchase_month = st.number_input(
                "Purchase Month",
                min_value=1,
                max_value=12,
                value=6
            )

        with col3:

            purchase_day_of_week = st.number_input(
                "Day of Week",
                min_value=0,
                max_value=6,
                value=2
            )

        with col4:

            purchase_hour = st.number_input(
                "Purchase Hour",
                min_value=0,
                max_value=23,
                value=14
            )

        # --------------------------------------------------
        # SUBMIT
        # --------------------------------------------------

        st.divider()

        submitted = st.form_submit_button(
            "🔮 Predict Delivery Delay",
            use_container_width=True
        )

    # --------------------------------------------------
    # PREDICTION
    # --------------------------------------------------

    if submitted:

        customer_state_code = next(
            (
                code
                for code, name in state_name_mapping.items()
                if name == customer_state_name
            ),
            customer_state_name
        )

        seller_state_code = next(
            (
                code
                for code, name in state_name_mapping.items()
                if name == seller_state_name
            ),
            seller_state_name
        )

        payload = {
            "customer_state": customer_state_code,
            "seller_state": seller_state_code,
            "product_category": product_category,
            "item_count": item_count,
            "total_price": total_price,
            "total_freight": total_freight,
            "unique_sellers": unique_sellers,
            "unique_products": unique_products,
            "total_weight_g": total_weight_g,
            "avg_weight_g": avg_weight_g,
            "max_weight_g": max_weight_g,
            "payment_count": payment_count,
            "total_payment_value": total_payment_value,
            "max_installments": max_installments,
            "payment_type": payment_type,
            "purchase_year": purchase_year,
            "purchase_month": purchase_month,
            "purchase_day_of_week": purchase_day_of_week,
            "purchase_hour": purchase_hour
        }

        try:

            response = requests.post(
                f"{FASTAPI_URL}/predict",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:

                result = response.json()

                st.success(
                    "Prediction completed successfully."
                )

                col1, col2 = st.columns(2)

                col1.metric(
                    "Delay Probability",
                    f"{result['delay_probability']:.2f}%"
                )

                if result["prediction"] == 1:

                    col2.error(
                        "⚠️ Prediction: Delayed"
                    )

                else:

                    col2.success(
                        "✅ Prediction: On Time"
                    )

            elif response.status_code == 422:

                st.error(
                    "Invalid input. Please check the values entered."
                )

            else:

                st.error(
                    f"API Error: {response.status_code}"
                )

        except requests.exceptions.ConnectionError:

            st.error(
                "Could not connect to FastAPI. "
                "Make sure the FastAPI server is running."
            )

        except Exception as e:

            st.error(
                f"Prediction failed: {e}"
            )


# ==================================================
# AI ASSISTANT PAGE
# ==================================================

else:

    st.title("🤖 AI Business Assistant")

    st.write(
        "Ask questions about orders, revenue, delivery, "
        "customers, and other business insights."
    )

    st.info(
        "The assistant combines the FastAPI backend, "
        "MySQL analytics, project knowledge, and a local Qwen3 language model."
    )

    st.subheader("💬 Ask a Question")

    question = st.text_area(
        "Your Question",
        placeholder=(
            "Example: How many orders were delayed?"
        ),
        height=120
    )

    ask_button = st.button(
        "🔍 Ask Assistant",
        use_container_width=True
    )

    if ask_button:

        if not question.strip():

            st.warning(
                "Please enter a question first."
            )

        else:

            try:

                with st.spinner("Analyzing your question..."):

                    response = requests.post(
                        f"{FASTAPI_URL}/ask-ai",
                        json={
                            "question": question
                        },
                        timeout=120
                    )

                if response.status_code == 200:

                    result = response.json()

                    st.subheader("💡 Assistant Response")

                    st.write(
                        result["answer"]
                    )

                    source = result.get("source")

                    if source == "MySQL":

                        st.caption(
                            "📊 Source: MySQL database"
                        )

                    elif source == "RAG + Qwen3":

                        st.caption(
                            "📚 Source: Project knowledge (RAG) + Qwen3"
                        )

                    elif source == "LLM + Guardrail":

                        st.caption(
                            "🛡️ Source: Qwen3 + application guardrail"
                        )

                    elif source == "LLM":

                        st.caption(
                            "🤖 Source: Qwen3 general reasoning"
                        )

                    else:

                        st.caption(
                            f"🤖 Source: {source}"
                        )

                elif response.status_code == 422:

                    st.error(
                        "Invalid question format."
                    )

                else:

                    st.error(
                        f"AI Assistant API Error: "
                        f"{response.status_code}"
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Could not connect to FastAPI. "
                    "Make sure the FastAPI server is running."
                )

            except requests.exceptions.Timeout:

                st.error(
                    "The AI response took too long. "
                    "Please try again."
                )

            except Exception as e:

                st.error(
                    f"AI Assistant failed: {e}"
                )
