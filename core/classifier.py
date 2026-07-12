"""
Classifier — Dispute classification and workflow lookup.
"""

from data.constants import DISPUTE_KEYWORDS, WORKFLOWS


import os
import json

# Setup NLP Pipeline if available
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "inlegalbert-dispute-classifier")
MAPPING_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "label_mapping.json")

classifier_pipeline = None
label_mapping = None

try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
    if os.path.exists(MODEL_DIR) and os.path.exists(MAPPING_FILE):
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
        classifier_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer)
        
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            mapping_data = json.load(f)
            # HF pipelines return labels like "LABEL_0", map them back to category names
            label_mapping = mapping_data.get("id2label", {})
except Exception as e:
    print(f"Warning: Could not load InLegalBERT model ({e}). Falling back to keyword matching.")

def classify_dispute_keywords(message: str) -> tuple[str, str, str]:
    """Fallback: Classify the dispute based on exact keyword matches."""
    msg_lower = message.lower()
    for keyword, (category, process, court) in DISPUTE_KEYWORDS.items():
        if keyword in msg_lower:
            return category, process, court
    return "General Civil Dispute", "Civil Recovery", "Civil Court"

def _get_court_details_for_category(category_name: str) -> tuple[str, str, str]:
    """Helper to get process and court for a known category title."""
    for keyword, (cat, process, court) in DISPUTE_KEYWORDS.items():
        if cat == category_name:
            return cat, process, court
    return category_name, "Civil Recovery", "Civil Court"

def classify_dispute(message: str) -> tuple[str, str, str]:
    """Classify the dispute using InLegalBERT, falling back to keywords."""
    if classifier_pipeline and label_mapping:
        try:
            # Run inference
            result = classifier_pipeline(message[:512])[0] # Truncate to avoid length errors
            
            # Extract label index (e.g. "LABEL_3" -> "3")
            label_idx = result["label"].replace("LABEL_", "")
            confidence = result["score"]
            
            # If the model is reasonably confident, use its prediction
            if confidence > 0.5:
                category_name = label_mapping.get(label_idx)
                if category_name:
                    return _get_court_details_for_category(category_name)
        except Exception as e:
            print(f"ML Classification error: {e}")

    # Fallback to precise keyword matching
    return classify_dispute_keywords(message)


def get_workflow(category: str) -> dict:
    """Get the workflow for a dispute category."""
    for key in WORKFLOWS:
        if key in category or category in key:
            return WORKFLOWS[key]
    # No match found — return a safe generic fallback
    return {
        "title": "General Civil Dispute",
        "steps": [
            "Document your complaint clearly with dates and facts",
            "Gather all relevant evidence and correspondence",
            "Send a legal notice to the opposing party",
            "Consult a lawyer to identify the correct court and procedure",
            "File the appropriate petition/complaint in the relevant court",
            "Attend hearings and present your evidence",
            "Receive court order or judgment",
        ],
        "documents_needed": ["Written complaint", "Supporting evidence", "ID Proof", "Any relevant agreements or correspondence"],
        "court_fee": "Varies by court and claim type",
        "time_estimate": "Varies",
        "questions": [
            ("opponent_name",    "Name of the opposing party"),
            ("opponent_address", "Their address"),
            ("dispute_details",  "Brief description of the dispute"),
            ("amount_involved",  "Amount or value involved (if any, in ₹)"),
        ]
    }
