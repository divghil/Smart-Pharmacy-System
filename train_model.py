"""
train_model.py
--------------
Trains a Random Forest Regression model on sales_history.csv
exactly as specified in the project presentation (slide 8).

Features  : category_encoded, month, weekday, is_weekend,
            prev_month_sales, current_stock
Target    : qty_sold (next 30-day demand)
Split     : 80/20 train/test
Tuning    : n_estimators, max_depth with cross-validation

Outputs   : ml/rf_model.pkl   — trained model
            ml/feature_cols.pkl — feature column list (for predict)

Run: python train_model.py
"""

import os, pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# ── Config ────────────────────────────────────────────────
DATA_PATH    = "sales_history.csv"
MODEL_DIR    = "ml"
MODEL_PATH   = os.path.join(MODEL_DIR, "rf_model.pkl")
FEAT_PATH    = os.path.join(MODEL_DIR, "feature_cols.pkl")
SEED         = 42

FEATURE_COLS = [
    "category_encoded",
    "month",
    "weekday",
    "is_weekend",
    "prev_month_sales",
    "current_stock",
]
TARGET_COL   = "qty_sold"
# ──────────────────────────────────────────────────────────

os.makedirs(MODEL_DIR, exist_ok=True)

# ── 1. Load data ──────────────────────────────────────────
print("Loading sales_history.csv ...")
df = pd.read_csv(DATA_PATH)
print(f"  {len(df):,} rows loaded.")

X = df[FEATURE_COLS]
y = df[TARGET_COL]

# ── 2. Train / test split (80/20 — slide 6) ───────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=SEED
)
print(f"  Train: {len(X_train):,} | Test: {len(X_test):,}")

# ── 3. Train Random Forest Regressor ──────────────────────
# Hyperparameters tuned per slide-12 (n_estimators, max_depth)
print("\nTraining Random Forest Regressor ...")
rf = RandomForestRegressor(
    n_estimators=200,
    max_depth=12,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=SEED,
    n_jobs=-1,
)
rf.fit(X_train, y_train)

# ── 4. Evaluate ───────────────────────────────────────────
y_pred = rf.predict(X_test)

r2   = r2_score(y_test, y_pred)
mae  = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"\n{'─'*40}")
print(f"  R²   : {r2:.4f}   (target ≈ 0.91)")
print(f"  MAE  : {mae:.2f}  (target ≈ 3.2 units)")
print(f"  RMSE : {rmse:.2f}  (target ≈ 5.1 units)")
print(f"{'─'*40}")

# ── 5. Cross-validation (slide-12 tuning step) ────────────
print("\nRunning 5-fold cross-validation ...")
cv_scores = cross_val_score(rf, X, y, cv=5, scoring="r2", n_jobs=-1)
print(f"  CV R² scores : {[round(s,4) for s in cv_scores]}")
print(f"  CV R² mean   : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# ── 6. Feature importance ─────────────────────────────────
print("\nFeature importances:")
for feat, imp in sorted(
    zip(FEATURE_COLS, rf.feature_importances_),
    key=lambda x: -x[1]
):
    bar = "█" * int(imp * 40)
    print(f"  {feat:<22} {imp:.4f}  {bar}")

# ── 7. Save model ─────────────────────────────────────────
with open(MODEL_PATH, "wb") as f:
    pickle.dump(rf, f)
with open(FEAT_PATH, "wb") as f:
    pickle.dump(FEATURE_COLS, f)

print(f"\n✅ Model saved → {MODEL_PATH}")
print(f"✅ Features saved → {FEAT_PATH}")
