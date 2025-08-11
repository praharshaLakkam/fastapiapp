from fastapi import APIRouter
from models.request_models import QueryRequest
from transformers import pipeline

router = APIRouter()

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

@router.post("/detect")
def detect_intent(data: QueryRequest):
    question = data.question

    candidate_intents = ["status", "reason_of_failure", "success","buy"]
    result = classifier(question, candidate_labels=candidate_intents)
    top_intent = result["labels"][0]
    confidence = result["scores"][0]

    return {
        "intent": top_intent,
        "confidence": round(confidence, 4)
    }
