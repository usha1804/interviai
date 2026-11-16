"""Prompt-size safeguards for interview report generation."""
import json
import math
import re
from typing import Any
from app.config import settings


REPORT_MAX_PROMPT_CHARS = max(1000, settings.REPORT_MAX_PROMPT_CHARS)
REPORT_MAX_INPUT_TOKENS = max(500, settings.REPORT_MAX_INPUT_TOKENS)
REPORT_MAX_PAYLOAD_BYTES = max(2000, settings.REPORT_MAX_PAYLOAD_BYTES)
REPORT_MAX_ANSWER_CHARS = max(200, settings.REPORT_MAX_ANSWER_CHARS)
REPORT_MAX_BATCH_ANSWERS = max(1, settings.REPORT_MAX_BATCH_ANSWERS)
REPORT_MAX_CONTEXT_CHARS = max(200, settings.REPORT_MAX_CONTEXT_CHARS)


def estimate_prompt_tokens(text: str, model: str = "") -> int:
    """Estimate input tokens with tiktoken when installed, otherwise conservatively."""
    try:
        import tiktoken

        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except ImportError:
        return math.ceil(len(text) / 3.5)


def request_payload_size(model: str, prompt: str, max_tokens: int) -> int:
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    return len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def prompt_within_limits(prompt: str, model: str, max_tokens: int = 2000) -> bool:
    return (
        len(prompt) <= REPORT_MAX_PROMPT_CHARS
        and estimate_prompt_tokens(prompt, model) <= REPORT_MAX_INPUT_TOKENS
        and request_payload_size(model, prompt, max_tokens) <= REPORT_MAX_PAYLOAD_BYTES
    )


def split_text_preserving_content(text: str, max_chars: int) -> list[str]:
    """Split at a nearby sentence/whitespace boundary without dropping characters."""
    if not text:
        return [""]
    parts = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            floor = start + max(1, max_chars // 2)
            boundary = max(
                text.rfind("\n", floor, end),
                text.rfind(". ", floor, end),
                text.rfind("? ", floor, end),
                text.rfind("! ", floor, end),
                text.rfind(" ", floor, end),
            )
            if boundary > start:
                end = boundary + (1 if text[boundary] in ".?!" else 0)
        parts.append(text[start:end])
        start = end
    return parts


def select_relevant_context(context: str, query: str, max_chars: int = REPORT_MAX_CONTEXT_CHARS) -> str:
    """Keep deduplicated, query-relevant complete sentences from retrieved RAG chunks."""
    query_terms = {word for word in re.findall(r"\w+", query.casefold()) if len(word) > 2}
    candidates = []
    seen = set()
    for chunk_index, chunk in enumerate(context.split("\n\n")):
        for sentence_index, sentence in enumerate(re.split(r"(?<=[.!?])\s+", chunk.strip())):
            sentence = sentence.strip()
            normalized = " ".join(sentence.casefold().split())
            if not sentence or normalized in seen:
                continue
            seen.add(normalized)
            words = set(re.findall(r"\w+", normalized))
            relevance = len(query_terms & words)
            if query_terms and relevance == 0:
                continue
            candidates.append((relevance, chunk_index, sentence_index, sentence))

    selected = []
    used = 0
    for _, _, _, sentence in sorted(candidates, key=lambda item: (-item[0], item[1], item[2])):
        extra = len(sentence) + (1 if selected else 0)
        if used + extra > max_chars:
            continue
        selected.append(sentence)
        used += extra
    return " ".join(selected)
