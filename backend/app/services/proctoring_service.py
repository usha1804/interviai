"""
Centralized Interview Proctoring Service

Receives aggregated events from frontend (tab switches, copy/paste,
face metrics, fullscreen exits) and computes:
  - Proctoring Score  (integrity — penalises violations)
  - Confidence Score  (behaviour — eye contact, posture, expression)
  - AI Feedback       (Groq generated HR assessment)
"""
import json
from app.config import settings
from app.services.ai_service import _chat, get_groq_client


def compute_proctoring_score(violations: dict) -> float:
    """
    Start at 100, deduct per violation type.
    violations keys: tab_switches, copy_paste_count, face_not_detected,
                     multiple_faces, fullscreen_exits, looking_away
    """
    score = 100.0
    score -= min(violations.get("tab_switches", 0) * 8, 40)
    score -= min(violations.get("copy_paste_count", 0) * 5, 25)
    score -= min(violations.get("face_not_detected", 0) * 3, 20)
    score -= min(violations.get("multiple_faces", 0) * 10, 30)
    score -= min(violations.get("fullscreen_exits", 0) * 6, 24)
    score -= min(violations.get("looking_away", 0) * 2, 20)
    return round(max(score, 0), 1)


def compute_confidence_score(metrics: dict) -> dict:
    """
    metrics keys: eye_contact_pct, attention_pct, movement_score, smile_pct
    Returns all four sub-scores + composite confidence.
    """
    eye = float(metrics.get("eye_contact_pct", 70))
    attention = float(metrics.get("attention_pct", 70))
    movement = float(metrics.get("movement_score", 30))
    smile = float(metrics.get("smile_pct", 40))

    posture = max(0, min(100, 100 - movement))
    expression = smile * 0.4 + attention * 0.6
    confidence = eye * 0.35 + posture * 0.25 + expression * 0.25 + attention * 0.15

    return {
        "eye_contact_score": round(eye, 1),
        "posture_score": round(posture, 1),
        "expression_score": round(expression, 1),
        "confidence_score": round(confidence, 1),
    }


def generate_proctoring_feedback(scores: dict, violations: dict, session_type: str) -> dict:
    client = get_groq_client()
    prompt = f"""You are an expert HR Interview Assessor reviewing a candidate's interview integrity and behaviour.

Session Type: {session_type}

Behavioural Scores (0-100):
- Confidence:   {scores.get('confidence_score', 0)}
- Eye Contact:  {scores.get('eye_contact_score', 0)}
- Posture:      {scores.get('posture_score', 0)}
- Expression:   {scores.get('expression_score', 0)}

Integrity Violations:
- Tab switches:        {violations.get('tab_switches', 0)}
- Copy/paste events:   {violations.get('copy_paste_count', 0)}
- Face not detected:   {violations.get('face_not_detected', 0)}
- Multiple faces:      {violations.get('multiple_faces', 0)}
- Fullscreen exits:    {violations.get('fullscreen_exits', 0)}
- Looking away events: {violations.get('looking_away', 0)}

Generate a professional assessment.

Return ONLY this JSON:
{{
    "overall_assessment": "<2-3 sentence summary>",
    "integrity_verdict": "<Clean / Minor Issues / Suspicious / Flagged>",
    "strengths": ["<s1>", "<s2>"],
    "concerns": ["<c1>", "<c2>"],
    "recommendations": ["<r1>", "<r2>"]
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=600)
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e])
    except Exception:
        return {
            "overall_assessment": "Session completed. Review violations for integrity.",
            "integrity_verdict": "Clean",
            "strengths": ["Maintained composure"],
            "concerns": [],
            "recommendations": ["Keep consistent eye contact with the camera"],
        }


def generate_readiness_report(scores: dict) -> dict:
    """Generate final Interview Readiness Report combining all scores."""
    client = get_groq_client()

    prompt = f"""You are an expert Interview Coach generating a final readiness report.

Interview Performance Scores (0-100):
- Technical Score:      {scores.get('technical_score', 0)}
- Coding Score:         {scores.get('coding_score', 0)}
- Communication Score:  {scores.get('communication_score', 0)}
- Confidence Score:     {scores.get('confidence_score', 0)}
- Proctoring Score:     {scores.get('proctoring_score', 0)}

Calculate overall readiness and give actionable advice.

Return ONLY this JSON:
{{
    "readiness_score": <weighted average 0-100>,
    "readiness_level": "<Not Ready / Needs Practice / Almost Ready / Interview Ready / Exceptional>",
    "summary": "<3-4 sentence holistic assessment>",
    "top_strengths": ["<s1>", "<s2>", "<s3>"],
    "priority_improvements": ["<i1>", "<i2>", "<i3>"],
    "next_steps": ["<step1>", "<step2>"]
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=700)
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e])
    except Exception:
        avg = sum(scores.values()) / max(len(scores), 1)
        return {
            "readiness_score": round(avg, 1),
            "readiness_level": "Needs Practice",
            "summary": "Keep practising across all areas.",
            "top_strengths": ["Participation"],
            "priority_improvements": ["Technical depth", "Confidence"],
            "next_steps": ["Daily mock interviews", "Review weak topics"],
        }
