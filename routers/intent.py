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
# Order ID detection
# ----------------------------
ORDER_ID_PATTERN = r"\b(?:MSP|SFDC|RA|ECM|RSL)\d{8,}\b"

def contains_order_id(text: str) -> bool:
    return bool(re.search(ORDER_ID_PATTERN, text, re.IGNORECASE))

# ----------------------------
# Fix intent keyword detection
# ----------------------------
FIX_KEYWORDS = [
    "fix", "correct", "modify", "change", "update", "edit",
    "revise", "adjust", "amend", "repair"
]

def contains_fix_terms(text: str) -> bool:
    return any(re.search(rf"\b{kw}\b", text.lower()) for kw in FIX_KEYWORDS)

# ----------------------------
# Rule-based booster
# ----------------------------
def rule_boost(question: str, ml_intent: str) -> str:
    q_lower = question.lower()

    # 1. Fix keywords take priority over everything
    if contains_fix_terms(question):
        return "fix"

    # 2. Order IDs or explicit "order status" queries
    if contains_order_id(question) or "order status" in q_lower:
        return "order status"

    # 3. Quantities + product names => BUY
    if re.search(r"\b\d+\b", q_lower):
        if any(prod in q_lower for prod in ["saep", "sdns", "pillr", "dns"]):
            return "buy"

    # 4. Product names without failure keywords => BUY
    if any(prod in q_lower for prod in ["saep", "sdns", "pillr", "dns"]):
        if not any(word in q_lower for word in ["fail", "error", "issue", "problem", "repair"]):
            return "buy"

    return ml_intent

# ----------------------------
# Intent labels
# ----------------------------
candidate_intents = [
    "Customer wants order support or help with an existing cybersecurity product order (saep, sdns, pillr)",
    "Customer wants to place a new order for cybersecurity products (saep, sdns, pillr)",
    "Customer wants to fix or modify details of an existing cybersecurity product order (saep, sdns, pillr)"
]

intent_mapping = {
    candidate_intents[0]: "order status",
    candidate_intents[1]: "buy",
    candidate_intents[2]: "fix"
}

# ----------------------------
# Main API endpoint
# ----------------------------
@router.post("/detect")
def detect_intent(data: QueryRequest):
    question = data.question.strip()

    # Step 1: Zero-shot intent classification
    try:
        intent_result = classifier(
            question,
            candidate_labels=candidate_intents,
            multi_label=False
        )
    except Exception as e:
        return {
            "intent": "order status",
            "confidence": 0.0,
            "reason": f"Intent classification failed: {str(e)}"
        }

    if not intent_result.get("labels"):
        return {
            "intent": "order status",
            "confidence": 0.0,
            "reason": "Model returned no intent labels"
        }

    predicted_label = intent_result["labels"][0]
    confidence = intent_result["scores"][0]
    ml_intent = intent_mapping.get(predicted_label, "order status")

    # Step 2: Apply rule-based booster
    final_intent = rule_boost(question, ml_intent)

    # Step 3: Return final response
    return {
        "intent": final_intent,
        "confidence": round(float(confidence), 4),
        "raw_top_label": predicted_label
    }
