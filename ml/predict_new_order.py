import joblib
import pandas as pd

# Load trained model
model = joblib.load("delivery_delay_model.pkl")
print("Model loaded successfully!")

# Get new order details from user
customer_state = input("Enter customer state (e.g. SP): ")
seller_state = input("Enter seller state (e.g. SP): ")
product_category = input("Enter product category (e.g. health_beauty): ")
item_count = int(input("Enter item count: "))
total_price = float(input("Enter total price: "))
total_freight = float(input("Enter total freight: "))
unique_sellers = int(input("Enter number of unique sellers: "))
unique_products = int(input("Enter number of unique products: "))
total_weight_g = float(input("Enter total weight (g): "))
avg_weight_g = float(input("Enter average weight (g): "))
max_weight_g = float(input("Enter maximum weight (g): "))
payment_count = int(input("Enter payment count: "))
total_payment_value = float(input("Enter total payment value: "))
max_installments = int(input("Enter maximum installments: "))
payment_type = input("Enter payment type (e.g. credit_card): ")
purchase_year = int(input("Enter purchase year: "))
purchase_month = int(input("Enter purchase month: "))
purchase_day_of_week = int(input("Enter day of week (0=Monday, 6=Sunday): "))
purchase_hour = int(input("Enter purchase hour (0-23): "))

# Create new order dictionary
new_order = {
    "customer_state": customer_state,
    "seller_state": seller_state,
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

# Convert new order into DataFrame
new_order_df = pd.DataFrame([new_order])

# One-hot encode categorical columns
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

# Load feature columns used during training
feature_columns = joblib.load("delivery_model_features.pkl")

# Make new order match training columns
new_order_df = new_order_df.reindex(
    columns=feature_columns,
    fill_value=0
)
print("\nFeatures aligned successfully!")
print("New order shape:", new_order_df.shape)

# Predict delay probability
prediction_probability = model.predict_proba(new_order_df)[0][1]

# Use threshold of 0.6
prediction = 1 if prediction_probability >= 0.6 else 0
print("\nDelay probability:", round(prediction_probability * 100, 2), "%")
print("Prediction:", prediction)
if prediction == 1:
    print("⚠️ This order is predicted to be DELAYED.")
else:
    print("✅ This order is predicted to NOT be delayed.")

