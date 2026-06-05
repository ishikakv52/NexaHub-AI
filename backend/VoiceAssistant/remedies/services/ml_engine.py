import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# =========================
# TRAINING DATA (STARTER)
# =========================

TRAIN_DATA = [
    ("I have headache and fever", "medical"),
    ("sir dard ho raha hai", "medical"),
    ("mujhe bukhar hai", "medical"),
    ("I feel fine", "general"),
    ("what is the weather", "general"),
    ("play music", "general")
]

texts = [t[0] for t in TRAIN_DATA]
labels = [t[1] for t in TRAIN_DATA]

# =========================
# MODEL PIPELINE
# =========================

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

model = LogisticRegression()
model.fit(X, labels)


def predict_intent(text):
    X_input = vectorizer.transform([text])
    pred = model.predict(X_input)[0]
    return pred