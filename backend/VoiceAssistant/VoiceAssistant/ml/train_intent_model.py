"""
NEXA HUB — Intent Model Trainer (Enhanced)
Loads all dataset JSONs + Q&A training data
Trains TF-IDF + Logistic Regression pipeline
Run: python train_intent_model.py
"""

import os
import sys
import json
import glob

# ── Path setup ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE_DIR))

from ml_intent_model import MLIntentModel

DATASET_DIR = os.path.join(
    BASE_DIR, "datasets", "healthcare", "fitness_tracker"
)

# ── Q&A training utterances (built-in, no JSON file needed) ───
QA_TRAINING_DATA = [
    # qa_improve
    ("improve kaise kare", "qa_improve"),
    ("better kaise banaye", "qa_improve"),
    ("kaise sudhar sakta hai", "qa_improve"),
    ("tips do improvement ke liye", "qa_improve"),
    ("improve tips chahiye", "qa_improve"),
    ("advice do health ke liye", "qa_improve"),
    ("suggest karo kya karu", "qa_improve"),
    ("how can i improve this", "qa_improve"),
    ("kya karna chahiye improve karne ke liye", "qa_improve"),
    ("help me get better", "qa_improve"),
    ("improvement ke liye kya karu", "qa_improve"),
    ("aur better kaise hoga", "qa_improve"),
    ("best way to improve", "qa_improve"),
    ("kaise improve kare apni health", "qa_improve"),
    ("tips for better results", "qa_improve"),
    ("performance improve kaise kare", "qa_improve"),
    ("kya change karna chahiye", "qa_improve"),
    ("kaise behtar kar sakte hain", "qa_improve"),
    ("suggest lifestyle changes", "qa_improve"),
    ("better hone ke liye kya kare", "qa_improve"),

    # qa_compare
    ("compare karo last week se", "qa_compare"),
    ("yesterday se compare karo", "qa_compare"),
    ("pichle hafte se zyada hai kya", "qa_compare"),
    ("kitna badla hai", "qa_compare"),
    ("difference kya hai", "qa_compare"),
    ("last week vs this week", "qa_compare"),
    ("pehle aur ab mein difference", "qa_compare"),
    ("previous data se compare karo", "qa_compare"),
    ("kya improve hua hai", "qa_compare"),
    ("before and after comparison", "qa_compare"),
    ("trend kya hai upar ya neeche", "qa_compare"),
    ("is week better tha ya last week", "qa_compare"),
    ("kitni progress hui hai", "qa_compare"),
    ("improvement hua hai kya pichle hafte se", "qa_compare"),
    ("compare with yesterday", "qa_compare"),

    # qa_goal_check
    ("goal kab achieve hoga", "qa_goal_check"),
    ("target kab milega", "qa_goal_check"),
    ("kab tak goal complete hoga", "qa_goal_check"),
    ("goal reach karne mein kitna time", "qa_goal_check"),
    ("goal met hua kya", "qa_goal_check"),
    ("target achieve hua ya nahi", "qa_goal_check"),
    ("kitna baki hai goal se", "qa_goal_check"),
    ("goal complete karne ki date kya hai", "qa_goal_check"),
    ("how long to reach my goal", "qa_goal_check"),
    ("when will i achieve my target", "qa_goal_check"),
    ("goal kab poora hoga", "qa_goal_check"),
    ("target date kya hai", "qa_goal_check"),
    ("on track for goal kya main", "qa_goal_check"),
    ("goal progress kya hai", "qa_goal_check"),
    ("kitne din aur lagenge goal tak", "qa_goal_check"),

    # qa_why
    ("kyu zaroori hai yeh", "qa_why"),
    ("yeh kyu hota hai", "qa_why"),
    ("reason kya hai iska", "qa_why"),
    ("cause kya hai", "qa_why"),
    ("why is this happening", "qa_why"),
    ("kyun low hai yeh", "qa_why"),
    ("kyun high hai yeh", "qa_why"),
    ("iska matlab kya hai", "qa_why"),
    ("why does this matter", "qa_why"),
    ("kya wajah hai", "qa_why"),
    ("explain karo kyu aisa hai", "qa_why"),
    ("yeh number ka matlab samjhao", "qa_why"),
    ("kyu important hai yeh metric", "qa_why"),
    ("kyun track karna chahiye ise", "qa_why"),
    ("reason batao iska", "qa_why"),

    # qa_impact
    ("health par kya effect hoga", "qa_impact"),
    ("body par kya impact hai", "qa_impact"),
    ("kya problems ho sakti hain", "qa_impact"),
    ("iska kya asar hoga", "qa_impact"),
    ("consequences kya honge", "qa_impact"),
    ("health pe kya fark padta hai", "qa_impact"),
    ("isse kya hoga body ko", "qa_impact"),
    ("what happens if this is low", "qa_impact"),
    ("what happens if this is high", "qa_impact"),
    ("is yeh dangerous", "qa_impact"),
    ("kya koi risk hai", "qa_impact"),
    ("long term effect kya hai", "qa_impact"),
    ("isse kya nuksan ho sakta hai", "qa_impact"),
    ("body pe impact batao", "qa_impact"),
    ("kya hoga agar aisa raha", "qa_impact"),

    # qa_predict
    ("next week prediction do", "qa_predict"),
    ("kal ka forecast kya hai", "qa_predict"),
    ("future mein kya hoga", "qa_predict"),
    ("trend kya rahega aage", "qa_predict"),
    ("predict karo mera performance", "qa_predict"),
    ("estimate karo next week ka", "qa_predict"),
    ("what will happen next week", "qa_predict"),
    ("aage kya expect kar sakta hoon", "qa_predict"),
    ("forecast kya hai mera", "qa_predict"),
    ("agar aisa raha to future mein kya", "qa_predict"),
    ("prediction chahiye next 7 days ke liye", "qa_predict"),
    ("trend analysis karo", "qa_predict"),
    ("kya main improve karunga", "qa_predict"),
    ("next month mein kya hoga", "qa_predict"),
    ("future performance ka estimate do", "qa_predict"),

    # qa_explain
    ("yeh kya hota hai explain karo", "qa_explain"),
    ("iska matlab kya hota hai", "qa_explain"),
    ("what is this metric", "qa_explain"),
    ("deep sleep kya hota hai", "qa_explain"),
    ("rem sleep kya hai", "qa_explain"),
    ("heart rate zone kya hota hai", "qa_explain"),
    ("recovery score kaise calculate hota hai", "qa_explain"),
    ("bmi kya hota hai", "qa_explain"),
    ("stress score kya hai", "qa_explain"),
    ("explain this number to me", "qa_explain"),
    ("samjhao yeh kya hai", "qa_explain"),
    ("kya matlab hai iska", "qa_explain"),
    ("what does this mean for my health", "qa_explain"),
    ("define karo is metric ko", "qa_explain"),
    ("yeh data kya bol raha hai", "qa_explain"),
]


def load_datasets(dataset_dir: str) -> list:
    """Load all JSON files from datasets directory."""
    samples = []
    pattern = os.path.join(dataset_dir, "*.json")
    files   = glob.glob(pattern)

    if not files:
        print(f"⚠️  No JSON files found in: {dataset_dir}")
        print("   Using built-in Q&A training data only.")
        return samples

    for fpath in sorted(files):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "intent" in item and "utterance" in item:
                        samples.append((item["utterance"], item["intent"]))
        except Exception as e:
            print(f"  ⚠️  Skip {os.path.basename(fpath)}: {e}")

    print(f"✅ Loaded {len(samples)} samples from {len(files)} JSON files")
    return samples


def train():
    print("=" * 55)
    print("  NEXA HUB — Intent Model Trainer (Enhanced)")
    print("=" * 55)

    # Load existing dataset samples
    dataset_samples = load_datasets(DATASET_DIR)

    # Add Q&A training data
    all_samples = dataset_samples + QA_TRAINING_DATA
    print(f"📊 Total training samples: {len(all_samples)}")
    print(f"   (Dataset: {len(dataset_samples)} | Q&A: {len(QA_TRAINING_DATA)})")

    if len(all_samples) < 10:
        print("❌ Too few samples to train. Add more data!")
        return

    texts  = [s[0] for s in all_samples]
    labels = [s[1] for s in all_samples]

    unique_intents = sorted(set(labels))
    print(f"🏷️  Unique intents: {len(unique_intents)}")
    for intent in unique_intents:
        count = labels.count(intent)
        print(f"     {intent}: {count} samples")

    print("\n🔄 Training model...")
    model = MLIntentModel()
    model.train(texts, labels)

    model_path = os.path.join(BASE_DIR, "intent_model.pkl")
    model.save(model_path)
    print(f"✅ Model saved: {model_path}")

    # Quick validation
    print("\n🧪 Quick validation:")
    test_cases = [
        ("aaj kitne steps", "steps_today"),
        ("sleep kitni hui", "sleep_duration"),
        ("improve kaise kare", "qa_improve"),
        ("compare last week se", "qa_compare"),
        ("goal kab milega", "qa_goal_check"),
        ("kyu zaroori hai yeh", "qa_why"),
        ("predict karo next week", "qa_predict"),
        ("weekly summary dikhao", "weekly_summary"),
    ]
    correct = 0
    for text, expected in test_cases:
        predicted = model.predict(text)
        status    = "✅" if predicted == expected else "❌"
        print(f"  {status} '{text}' → {predicted} (expected: {expected})")
        if predicted == expected:
            correct += 1

    accuracy = round(correct / len(test_cases) * 100, 1)
    print(f"\n📈 Validation accuracy: {accuracy}% ({correct}/{len(test_cases)})")
    print("=" * 55)
    print("Training complete! Model ready for use.")


if __name__ == "__main__":
    train()