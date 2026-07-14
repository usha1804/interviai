"""
Webcam / behavior analysis service.

OpenCV + MediaPipe run CLIENT-SIDE via the browser's MediaRecorder API.
The frontend sends aggregated frame metrics (eye contact %, expressions, etc.)
to this service which:
  1. Calculates composite scores
  2. Uses Groq AI to generate strengths/improvements feedback
  3. Persists the result
"""
import json
from typing import Optional
from groq import Groq
from app.config import settings
from app.services.ai_service import _chat


def compute_scores(metrics: dict) -> dict:
    """
    Compute composite behavioral scores from raw frame metrics.
    metrics keys expected from frontend:
      eye_contact_pct  (0-100)
      avg_expression   (neutral/happy/sad/angry/fear/surprise)
      movement_score   (0-100, lower = more stable)
      attention_pct    (0-100)
    """
    eye = float(metrics.get("eye_contact_pct", 70))
    attention = float(metrics.get("attention_pct", 70))
    movement = float(metrics.get("movement_score", 50))
    smile_pct = float(metrics.get("smile_pct", 40))

    # Posture score: inverse of movement (less movement = better posture)
    posture = max(0, min(100, 100 - movement))

    # Expression score: blend of smile & attention
    expression = (smile_pct * 0.4 + attention * 0.6)

    # Overall confidence composite
    confidence = (eye * 0.35 + posture * 0.25 + expression * 0.25 + attention * 0.15)

    return {
        "confidence_score": round(confidence, 1),
        "eye_contact_score": round(eye, 1),
        "posture_score": round(posture, 1),
        "expression_score": round(expression, 1),
    }


def generate_behavior_feedback(scores: dict) -> dict:
    """Use Groq to generate HR-style behavioral feedback from scores."""
    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = f"""You are an expert HR Interview Coach analyzing a candidate's interview behavior.

Behavioral Scores (out of 100):
- Confidence Score: {scores['confidence_score']}
- Eye Contact Score: {scores['eye_contact_score']}
- Posture Score: {scores['posture_score']}
- Expression Score: {scores['expression_score']}

Based on these scores, provide professional interview feedback.

Return ONLY this JSON:
{{
    "overall_assessment": "<2-3 sentence summary>",
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "improvements": ["<improvement 1>", "<improvement 2>", "<improvement 3>"],
    "tips": ["<actionable tip 1>", "<actionable tip 2>"]
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=800)
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {
            "overall_assessment": "Good overall presence. Keep practising.",
            "strengths": ["Maintained composure", "Good energy level"],
            "improvements": ["Improve eye contact", "Reduce excessive movement"],
            "tips": ["Look directly at the camera", "Sit straight and still"],
        }
