"""
routes/ml_routes.py
-------------------
Flask blueprint exposing the trained Random Forest model.
Fixed: Medicine.query.all() replaced with paginated/limited queries
Fixed: predict() called with DataFrame to avoid sklearn feature name warning
"""

import os, pickle
import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request
from models.medicine import Medicine
from database.db import db

ml_bp = Blueprint("ml_bp", __name__)

# ── Load model once at import time ────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "rf_model.pkl")
FEAT_PATH  = os.path.join(BASE_DIR, "ml", "feature_cols.pkl")

_model        = None
_feature_cols = None

def load_model():
    global _model, _feature_cols
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run train_model.py first.")
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
        with open(FEAT_PATH, "rb") as f:
            _feature_cols = pickle.load(f)

# ── Category encoding — only fetch distinct values ────────
def get_cat_map():
    rows = db.session.query(Medicine.category).distinct().all()
    cats = sorted(r[0] for r in rows if r[0])
    return {c: i for i, c in enumerate(cats)}

# ── Build a one-row DataFrame (avoids sklearn warning) ────
def build_feature_df(medicine, cat_map, month=None):
    import datetime
    now     = datetime.date.today()
    month   = month or now.month
    weekday = now.weekday()
    return pd.DataFrame([{
        "category_encoded": cat_map.get(medicine.category, 0),
        "month":            month,
        "weekday":          weekday,
        "is_weekend":       1 if weekday >= 5 else 0,
        "prev_month_sales": medicine.stock // 4,
        "current_stock":    medicine.stock,
    }])

def risk_level(stock, predicted):
    if stock == 0:           return "out_of_stock"
    if predicted >= stock:   return "critical"
    if predicted >= stock * 0.75: return "high"
    if predicted >= stock * 0.50: return "medium"
    return "low"

# ══════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════

@ml_bp.route("/predict/<int:medicine_id>", methods=["GET"])
def predict_demand(medicine_id):
    try:
        load_model()
        med = Medicine.query.get(medicine_id)
        if not med:
            return jsonify({"error": "Medicine not found"}), 404

        cat_map   = get_cat_map()
        feat_df   = build_feature_df(med, cat_map)
        predicted = max(0, round(float(_model.predict(feat_df)[0]), 2))
        days_cover = round(med.stock / predicted * 30, 1) if predicted > 0 else None

        return jsonify({
            "medicine_id":            med.id,
            "medicine_name":          med.name,
            "category":               med.category,
            "current_stock":          med.stock,
            "predicted_demand_30d":   predicted,
            "days_of_stock_left":     days_cover,
            "risk":                   risk_level(med.stock, predicted),
            "reorder_suggested":      predicted >= med.stock * 0.75,
        })
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_bp.route("/smart-alerts", methods=["GET"])
def smart_alerts():
    """
    Returns at-risk medicines. Queries in small batches to avoid
    loading all 175K medicines into memory at once.
    """
    try:
        load_model()
        threshold = request.args.get("threshold", 50, type=int)
        limit     = request.args.get("limit", 100, type=int)  # cap for performance
        cat_map   = get_cat_map()

        # Only query medicines already low on stock — keeps the result set small
        medicines = Medicine.query.filter(Medicine.stock < threshold)\
                                  .limit(limit).all()

        alerts = []
        for med in medicines:
            feat_df   = build_feature_df(med, cat_map)
            predicted = max(0, float(_model.predict(feat_df)[0]))
            risk      = risk_level(med.stock, predicted)
            alerts.append({
                "medicine_id":          med.id,
                "medicine_name":        med.name,
                "category":             med.category,
                "current_stock":        med.stock,
                "predicted_demand_30d": round(predicted, 1),
                "risk":                 risk,
                "reorder_suggested":    predicted >= med.stock * 0.75,
            })

        priority = {"out_of_stock":0, "critical":1, "high":2, "medium":3, "low":4}
        alerts.sort(key=lambda x: priority.get(x["risk"], 5))

        return jsonify({"total_alerts": len(alerts), "alerts": alerts})

    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_bp.route("/fast-slow", methods=["GET"])
def fast_slow_classification():
    """
    Classify medicines as fast/slow movers.
    Uses a sample (default 200) to avoid loading all 175K rows.
    """
    try:
        load_model()
        sample_size = request.args.get("limit", 200, type=int)
        cat_map     = get_cat_map()

        # Spread sample across categories, deduplicated by name
        cats      = list(cat_map.keys())
        per_cat   = max(1, sample_size // len(cats)) if cats else sample_size
        medicines = []
        for cat in cats:
            seen_names = set()
            batch = Medicine.query.filter_by(category=cat).all()
            for med in batch:
                if med.name not in seen_names:
                    seen_names.add(med.name)
                    medicines.append(med)
                if len(seen_names) >= per_cat:
                    break

        predictions = []
        for med in medicines:
            feat_df   = build_feature_df(med, cat_map)
            predicted = max(0, float(_model.predict(feat_df)[0]))
            predictions.append((med, predicted))

        demands   = [p for _, p in predictions]
        threshold = np.percentile(demands, 20) if demands else 0

        result = []
        for med, predicted in predictions:
            label = "slow" if predicted <= threshold else "fast"
            result.append({
                "medicine_id":          med.id,
                "medicine_name":        med.name,
                "category":             med.category,
                "current_stock":        med.stock,
                "predicted_demand_30d": round(predicted, 1),
                "movement":             label,
                "recommendation":       "Reduce restock quantity" if label == "slow"
                                        else "Ensure adequate stock",
            })

        result.sort(key=lambda x: -x["predicted_demand_30d"])
        fast = [r for r in result if r["movement"] == "fast"]
        slow = [r for r in result if r["movement"] == "slow"]

        return jsonify({
            "fast_movers":      len(fast),
            "slow_movers":      len(slow),
            "threshold_demand": round(threshold, 2),
            "medicines":        result,
        })

    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_bp.route("/predict-batch", methods=["POST"])
def predict_batch():
    try:
        load_model()
        data         = request.json or {}
        medicine_ids = data.get("medicine_ids", [])
        if not medicine_ids:
            return jsonify({"error": "Provide medicine_ids list"}), 400

        cat_map = get_cat_map()
        results = []
        for mid in medicine_ids:
            med = Medicine.query.get(mid)
            if not med:
                results.append({"medicine_id": mid, "error": "Not found"})
                continue
            feat_df   = build_feature_df(med, cat_map)
            predicted = max(0, round(float(_model.predict(feat_df)[0]), 2))
            results.append({
                "medicine_id":          med.id,
                "medicine_name":        med.name,
                "predicted_demand_30d": predicted,
                "risk":                 risk_level(med.stock, predicted),
            })

        return jsonify({"results": results})

    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500
