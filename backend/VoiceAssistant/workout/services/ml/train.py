"""
train.py — ML model training pipeline (future integration).

To train:
    python manage.py shell -c "from workout.services.ml.train import train; train()"

Requires: scikit-learn, pandas, joblib
"""
from __future__ import annotations

from pathlib import Path


MODEL_PATH = Path(__file__).parent / "saved_models" / "workout_recommender.pkl"


def train(dataset_path: str = "datasets/workout_logs.json"):
    """
    Train a recommendation model from exported session data.
    Currently a stub — replace with real ML pipeline when data is sufficient.
    """
    try:
        import json
        import joblib
        import pandas as pd
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score
    except ImportError:
        raise ImportError(
            "ML training requires: pip install scikit-learn pandas joblib"
        )

    with open(dataset_path) as f:
        records = json.load(f)

    df = pd.DataFrame(records).dropna(subset=["user_rating"])

    feature_cols = [
        "age", "weight_kg", "height_cm", "bmi",
        "goal_encoded", "activity_type_encoded",
        "experience_encoded", "available_minutes",
    ]

    X = df[feature_cols]
    y = df["user_rating"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"Model accuracy: {acc:.2%}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

    return model