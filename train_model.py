import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Sample training dataset
data = {
    "credit_limit": [50000, 60000, 70000, 80000, 90000],
    "current_balance": [42000, 30000, 65000, 20000, 85000],
    "monthly_income": [40000, 50000, 60000, 45000, 70000],
    "num_transactions": [15, 10, 25, 8, 30],
    "late_payments": [5, 1, 10, 0, 15],
    "risk": [1, 0, 1, 0, 1]
}

df = pd.DataFrame(data)

# Features
X = df.drop("risk", axis=1)

# Target
y = df["risk"]

# Train model
model = RandomForestClassifier()
model.fit(X, y)

# Save model
joblib.dump(model, "model.pkl")

print("Model trained and saved as model.pkl")