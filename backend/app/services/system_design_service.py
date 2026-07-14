"""
System Design Interview Service
Generates architecture, scaling, DB, caching, and queue questions.
Evaluates answers on architecture, scalability, trade-offs, and tech choices.
"""
import json
from typing import Dict, List, Optional
from groq import Groq
from app.config import settings
from app.services.ai_service import _chat

SYSTEM_DESIGN_TOPICS = {
    "URL Shortener": "Design a URL shortening service like bit.ly",
    "WhatsApp": "Design a real-time messaging application like WhatsApp",
    "Uber": "Design a ride-sharing platform like Uber",
    "YouTube": "Design a video streaming platform like YouTube",
    "Netflix": "Design a video streaming and recommendation system like Netflix",
    "Instagram": "Design a photo-sharing social media platform like Instagram",
    "Food Delivery": "Design a food delivery platform like Swiggy/Zomato",
    "Chat Application": "Design a scalable chat application",
    "Inventory Management": "Design an inventory management system for e-commerce",
    "Microservices": "Design a microservices architecture for an e-commerce platform",
}

QUESTION_CATEGORIES = [
    "Architecture Overview",
    "Database Design",
    "Scalability & Load Balancing",
    "Caching Strategy",
    "Message Queue & Async Processing",
    "API Design",
    "Fault Tolerance & High Availability",
]


def generate_system_design_questions(topic: str, difficulty: str = "MEDIUM") -> List[Dict]:
    """Generate a set of system design questions for a given topic."""
    client = Groq(api_key=settings.GROQ_API_KEY)
    topic_desc = SYSTEM_DESIGN_TOPICS.get(topic, f"Design a {topic} system")

    prompt = f"""You are a Senior System Design Interviewer at a top tech company.

Topic: {topic_desc}
Difficulty: {difficulty}

Generate 5 progressive system design interview questions covering:
1. High-level architecture
2. Database design and data modeling
3. Scalability and performance
4. Caching and optimization
5. Trade-offs and technology choices

Return ONLY this JSON:
{{
    "questions": [
        {{
            "id": 1,
            "category": "<category>",
            "question": "<question text>",
            "follow_up": "<follow-up probe question>",
            "evaluation_criteria": ["<criterion1>", "<criterion2>"]
        }}
    ]
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=2000)
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e]).get("questions", [])
    except Exception:
        return []


def evaluate_system_design_answer(
    topic: str,
    question: str,
    answer: str,
    question_category: str,
) -> Dict:
    """Evaluate a system design answer across multiple dimensions."""
    client = Groq(api_key=settings.GROQ_API_KEY)

    prompt = f"""You are a Senior System Design Interviewer evaluating a candidate's answer.

Topic: {topic}
Question Category: {question_category}
Question: {question}
Candidate's Answer: {answer}

Evaluate on these dimensions (0-10 each):
- Architecture: clarity and correctness of design
- Scalability: ability to handle growth
- Trade-offs: awareness of pros/cons
- Technology Choices: appropriateness of tech stack

Return ONLY this JSON:
{{
    "architecture_score": <0-10>,
    "scalability_score": <0-10>,
    "tradeoffs_score": <0-10>,
    "tech_choices_score": <0-10>,
    "overall_score": <0-10>,
    "strengths": ["<s1>", "<s2>"],
    "gaps": ["<g1>", "<g2>"],
    "ideal_approach": "<2-3 sentence model answer>",
    "feedback": "<detailed 2-3 paragraph feedback>"
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=1200)
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e])
    except Exception:
        return {
            "architecture_score": 5, "scalability_score": 5,
            "tradeoffs_score": 5, "tech_choices_score": 5,
            "overall_score": 5, "strengths": [], "gaps": [],
            "ideal_approach": "N/A", "feedback": "Evaluation unavailable.",
        }


def generate_final_system_design_report(topic: str, qa_pairs: List[Dict]) -> Dict:
    """Generate overall system design performance report."""
    client = Groq(api_key=settings.GROQ_API_KEY)
    summary = "\n".join(
        f"Q: {p['question']}\nA: {p['answer']}\nScore: {p.get('score', 0)}/10"
        for p in qa_pairs
    )

    prompt = f"""You are evaluating a complete system design interview for: {topic}

Interview Transcript:
{summary}

Return ONLY this JSON:
{{
    "overall_score": <0-100>,
    "architecture_score": <0-100>,
    "scalability_score": <0-100>,
    "tradeoffs_score": <0-100>,
    "strengths": ["<s1>", "<s2>"],
    "weaknesses": ["<w1>", "<w2>"],
    "topics_to_study": ["<t1>", "<t2>", "<t3>"],
    "ai_summary": "<3-4 sentence executive summary>"
}}"""

    text = _chat(client, settings.GROQ_MODEL, prompt, max_tokens=1000)
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e])
    except Exception:
        return {
            "overall_score": 60, "architecture_score": 60,
            "scalability_score": 60, "tradeoffs_score": 60,
            "strengths": [], "weaknesses": [], "topics_to_study": [],
            "ai_summary": "Report unavailable.",
        }
