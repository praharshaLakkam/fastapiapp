# routers/intent_router.py

from fastapi import APIRouter
from models.request_models import QueryRequest
from transformers import pipeline
import re

router = APIRouter()

# ============================
# Load improved zero-shot model
# ============================
classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/deberta-v3-large-zeroshot-v2.0",
    hypothesis_template="The customer request is about {}."
)

# ----------------------------
# Travel keyword filter
# ----------------------------
TRAVEL_KEYWORDS = [
    "flight", "train", "bus", "ticket", "visa", "airport",
    "london", "paris", "dubai", "travel", "trip", "holiday"
]

def contains_travel_terms(text: str) -> bool:
    return any(re.search(rf"\b{kw}\b", text.lower()) for kw in TRAVEL_KEYWORDS)

# ----------------------------
# Order ID detection
# ----------------------------
ORDER_ID_PATTERN = r"\b(?:MSP|SFDC|RA|ECM|RSL)\d{8,}\b"

def contains_order_id(text: str) -> bool:
    return bool(re.search(ORDER_ID_PATTERN, text, re.IGNORECASE))

# ----------------------------
# Fix intent keyword detection
# ----------------------------
FIX_KEYWORDS = [
    "fix", "correct", "modify", "change", "update", "edit", "revise", "adjust", "amend", "repair"
]

def contains_fix_terms(text: str) -> bool:
    return any(re.search(rf"\b{kw}\b", text.lower()) for kw in FIX_KEYWORDS)

# ----------------------------
# Rule-based booster
# ----------------------------
def rule_boost(question: str, ml_intent: str) -> str:
    q_lower = question.lower()

    # 1. Detect specific order IDs or order status inquiries => order status
    if contains_order_id(question) or "order status" in q_lower:
        return "order status"

    # 2. Detect fix-related terms => fix
    if contains_fix_terms(question):
        return "fix"

    # 3. Detect quantities + product names => BUY
    if re.search(r"\b\d+\b", q_lower):
        if any(prod in q_lower for prod in ["saep", "sdns", "pillr"]):
            return "buy"

    # 4. Product names without failure keywords => BUY
    if any(prod in q_lower for prod in ["saep", "sdns", "pillr"]):
        if not any(word in q_lower for word in ["fail", "error", "issue", "problem", "repair"]):
            return "buy"

    return ml_intent

# ----------------------------
# Relevance labels (cybersecurity)
# ----------------------------
relevance_labels = [
    "shopping for cybersecurity products like saep, sdns, pillr or checking an existing order",
    "travel, country visits, tickets, events, or anything unrelated to cybersecurity shopping"
]

# ----------------------------
# Intent labels
# ----------------------------
candidate_intents = [
    "Customer wants order support or help with an existing cybersecurity product order (saep, sdns, pillr)",
    "Customer wants to place a new order for cybersecurity products (saep, sdns, pillr)",
    "Customer wants to fix or modify details of an existing cybersecurity product order (saep, sdns, pillr)",
    "This query is unrelated to cybersecurity product orders or support"
]

intent_mapping = {
    candidate_intents[0]: "order status",
    candidate_intents[1]: "buy",
    candidate_intents[2]: "fix",
    candidate_intents[3]: "other"
}

# ----------------------------
# Main API endpoint
# ----------------------------
@router.post("/detect")
def detect_intent(data: QueryRequest):
    question = data.question.strip()

    # Step 0.1: Travel rejection
    if contains_travel_terms(question):
        return {
            "intent": "other",
            "confidence": 1.0,
            "reason": "Detected travel/ticket-related terms not relevant to cybersecurity products"
        }

    # Step 1: Relevance check
    try:
        relevance_result = classifier(
            question,
            candidate_labels=relevance_labels,
            multi_label=False
        )
    except Exception as e:
        return {
            "intent": "other",
            "confidence": 0.0,
            "reason": f"Relevance check failed: {str(e)}"
        }

    if not relevance_result.get("labels"):
        return {
            "intent": "other",
            "confidence": 0.0,
            "reason": "Model returned no relevance labels"
        }

    top_relevance_label = relevance_result["labels"][0]
    relevance_confidence = relevance_result["scores"][0]
    is_ecom_related = (
        top_relevance_label == relevance_labels[0]  and relevance_confidence >= 0.40
    )

    if not is_ecom_related:
        return {
            "intent": "other",
            "confidence": round(relevance_confidence, 4),
            "reason": "Not related to cybersecurity product ordering or support"
        }

    # Step 2: Zero-shot intent classification
    try:
        intent_result = classifier(
            question,
            candidate_labels=candidate_intents,
            multi_label=False
        )
    except Exception as e:
        return {
            "intent": "other",
            "confidence": 0.0,
            "reason": f"Intent classification failed: {str(e)}"
        }

    if not intent_result.get("labels"):
        return {
            "intent": "other",
            "confidence": 0.0,
            "reason": "Model returned no intent labels"
        }

    predicted_label = intent_result["labels"][0]
    confidence = intent_result["scores"][0]
    ml_intent = intent_mapping.get(predicted_label, "other")

    # Step 3: Apply rule-based booster
    final_intent = rule_boost(question, ml_intent)

    # Step 4: Confidence fallback
    if confidence < 0.5 and final_intent == ml_intent:
        final_intent = "other"

    # Step 5: Return final response
    return {
        "intent": final_intent,
        "confidence": round(float(confidence), 4),
        "raw_top_label": predicted_label
    }
