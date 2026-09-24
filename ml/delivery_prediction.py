import mysql.connector
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import shap
import joblib
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.metrics import roc_auc_score
from sklearn.metrics import roc_curve

# Connect to MySQL
conn = mysql.connector.connect(
    host="127.0.0.1",
    port=3307,
    user="root",
    password="kAyp@2323",
    database="olist_db"
)

# Load ML dataset from MySQL
query = "SELECT * FROM ml_order_features"

df = pd.read_sql(query, conn)

# Close connection
conn.close()

# Check the data
print("Shape:", df.shape)
print("\nFirst 5 rows:")
print(df.head())
print("\nColumns:")
print(df.columns.tolist())

# Convert purchase timestamp to datetime
df["order_purchase_timestamp"] = pd.to_datetime(
    df["order_purchase_timestamp"]
)

# Create useful time features
df["purchase_year"] = df["order_purchase_timestamp"].dt.year
df["purchase_month"] = df["order_purchase_timestamp"].dt.month
df["purchase_day_of_week"] = df["order_purchase_timestamp"].dt.dayofweek
df["purchase_hour"] = df["order_purchase_timestamp"].dt.hour

# Separate features and target
X = df.drop(columns=[
    "order_id",
    "is_delayed",
    "order_purchase_timestamp",
    "order_estimated_delivery_date"
])

y = df["is_delayed"]

print("\nX shape:", X.shape)
print("y shape:", y.shape)

print("\nData types:")
print(X.dtypes)

# Convert categorical columns into numerical columns
X = pd.get_dummies(
    X,
    columns=[
        "customer_state",
        "seller_state",
        "product_category",
        "payment_type"
    ],
    dtype=int
)
print("\nX shape after encoding:", X.shape)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\nTraining data:", X_train.shape)
print("Testing data:", X_test.shape)

# Create the XGBoost model
model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    scale_pos_weight=13.77,
    random_state=42,
    eval_metric="logloss"
)
# Train the model
model.fit(X_train, y_train)
joblib.dump(model, "delivery_delay_model.pkl")
joblib.dump(X.columns.tolist(), "delivery_model_features.pkl")
print("\nModel saved successfully!")
print("Feature columns saved successfully!")
print("\nXGBoost model trained successfully!")
explainer = shap.TreeExplainer(model)
X_shap = X_test.sample(1000, random_state=42)
shap_values = explainer.shap_values(X_shap)
shap.summary_plot(
    shap_values,
    X_shap,
    max_display=10
)

# Make probability predictions
y_prob = model.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_prob)
print("\nROC-AUC Score:", auc)
fpr, tpr, thresholds = roc_curve(y_test, y_prob)
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr)
plt.plot([0, 1], [0, 1], linestyle="--")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve - Delivery Delay Prediction")
plt.tight_layout()
plt.show()

# Use 0.6 as the final prediction threshold
y_pred = (y_prob >= 0.6).astype(int)
print("\nPredictions made successfully!")
print("First 10 predictions:")
print(y_pred[:10])

# Calculate accuracy
accuracy = accuracy_score(y_test, y_pred)
print("\nAccuracy:", accuracy)

# Detailed evaluation
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Confusion matrix
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Feature importance
importance = model.feature_importances_
feature_importance = pd.DataFrame({
    "feature": X.columns,
    "importance": importance
})
feature_importance = feature_importance.sort_values(
    by="importance",
    ascending=False
)
print("\nTop 10 Important Features:")
print(feature_importance.head(10))

# Select top 10 features
top_features = feature_importance.head(10)

# Create bar chart
plt.figure(figsize=(10, 6))
plt.barh(top_features["feature"], top_features["importance"])
plt.xlabel("Importance")
plt.ylabel("Feature")
plt.title("Top 10 Features for Delivery Delay Prediction")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()

ConfusionMatrixDisplay.from_predictions(
    y_test,
    y_pred,
    display_labels=["Not Delayed", "Delayed"]
)
plt.title("Confusion Matrix - Delivery Delay Prediction")
plt.tight_layout()
plt.show()

print("\n===== FINAL MODEL RESULTS =====")
print("Accuracy:", round(accuracy, 4))
print("ROC-AUC:", round(auc, 4))
print("Threshold:", 0.6)