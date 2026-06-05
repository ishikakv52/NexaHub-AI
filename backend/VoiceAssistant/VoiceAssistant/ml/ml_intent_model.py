"""
ML Intent Classifier — NexaHub AI (Enhanced)
TF-IDF + Logistic Regression
Includes Q&A intents for post-report questions
"""

import os
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder


class MLIntentModel:

    MODEL_PATH = "intent_model.pkl"

    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 3),
                min_df=1,
                max_df=0.95,
                strip_accents='unicode',
                analyzer='word',
                sublinear_tf=True,
            )),
            ('clf', LogisticRegression(
                max_iter=300,
                C=5.0,
                solver='lbfgs',
                multi_class='auto'
            ))
        ])
        self.label_encoder = LabelEncoder()
        self.trained = False

    def train(self, texts: list, labels: list):
        """Train on utterances + labels."""
        encoded = self.label_encoder.fit_transform(labels)
        self.pipeline.fit(texts, encoded)
        self.trained = True

    def predict(self, text: str) -> str | None:
        """Predict intent label."""
        if not self.trained:
            return None
        try:
            encoded = self.pipeline.predict([text])[0]
            return self.label_encoder.inverse_transform([encoded])[0]
        except Exception:
            return None

    def predict_proba(self, text: str) -> dict:
        """Return probability distribution over intents."""
        if not self.trained:
            return {}
        try:
            probs   = self.pipeline.predict_proba([text])[0]
            classes = self.label_encoder.classes_
            return {cls: round(float(prob), 4) for cls, prob in zip(classes, probs)}
        except Exception:
            return {}

    def save(self, path: str = None):
        path = path or self.MODEL_PATH
        with open(path, "wb") as f:
            pickle.dump((self.pipeline, self.label_encoder, self.trained), f)

    def load(self, path: str = None) -> bool:
        path = path or self.MODEL_PATH
        if not os.path.exists(path):
            return False
        try:
            with open(path, "rb") as f:
                self.pipeline, self.label_encoder, self.trained = pickle.load(f)
            return True
        except Exception:
            return False