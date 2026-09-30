import os
import re
import json

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL = "qwen/qwen3.8-27b"
MAX_CONTEXT_CHARS = 14000
MAX_HISTORY_MESSAGES = 4
MAX_CHARS_PER_HISTORY_MESSAGE = 1200


def _build_context(chunks, max_chars=MAX_CONTEXT_CHARS):
    selected = []
    total = 0

    for chunk in chunks:
        text = chunk.content.strip()

        if not text:
            continue

        remaining = max_chars - total

        if remaining <= 0:
            break

        if len(text) > remaining:
            text = text[:remaining]

        selected.append(
            f"[Page {chunk.page_number}]\n{text}"
        )

        total += len(text)

    return "\n\n".join(selected)


def _build_history(previous_messages):
    if not previous_messages:
        return ""

    history = []

    for message in previous_messages[-MAX_HISTORY_MESSAGES:]:
        question = message.question.strip()[:MAX_CHARS_PER_HISTORY_MESSAGE]
        answer = message.answer.strip()[:MAX_CHARS_PER_HISTORY_MESSAGE]

        history.append(
            f"User: {question}\nAssistant: {answer}"
        )

    return "\n\n".join(history)


def generate_answer(question: str, chunks, previous_messages=None):
    context = _build_context(chunks)
    history = _build_history(previous_messages)

    history_section = (
        f"\nPrevious conversation:\n{history}\n"
        if history
        else ""
    )

    prompt = f"""You are ASTRA, a grounded document intelligence assistant.

Answer ONLY from the provided document evidence.

Rules:
- Never use outside knowledge.
- Never invent, estimate, guess, or infer unsupported facts.
- Every factual statement must be supported by the evidence.
- Cite relevant page numbers naturally as [Page X].
- If related information is present but the exact requested fact is missing, explain what is present and clearly state that the exact fact is not provided.
- Do not calculate or derive a missing statistic, percentage, date, measurement, or value.
- Do not claim that the entire document lacks information when only the retrieved evidence lacks it.
- Answer every part of multi-part questions when evidence is available.
- For comparisons, cover each requested entity using only the evidence.
- Keep the answer concise and structured.

{history_section}
Document evidence:
{context}

Current question:
{question}

Return only the final answer.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=600
    )

    return response.choices[0].message.content.strip()


def compare_documents(document1_name, document2_name, chunks1, chunks2):
    max_chars_per_document = 6500

    context1 = _build_context(
        chunks1,
        max_chars=max_chars_per_document
    )

    context2 = _build_context(
        chunks2,
        max_chars=max_chars_per_document
    )

    prompt = f"""You are ASTRA INTEL, a grounded document comparison system.

Compare the two documents using ONLY the evidence provided.

DOCUMENT A:
{document1_name}

{context1}

DOCUMENT B:
{document2_name}

{context2}

Cover:
1. Main topics
2. Important similarities
3. Important differences
4. Distinct information found in either document

Use [Page X] references for factual claims.
Do not invent or infer unsupported information.
If information is not present in the provided evidence, say that it is not stated.

Return only the comparison.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=700
    )

    return response.choices[0].message.content.strip()


def _normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _content_tokens(text):
    return set(
        token
        for token in _normalize(text).split()
        if len(token) >= 4
    )


def _sentence_claims(answer):
    answer = re.sub(r"```.*?```", " ", answer, flags=re.DOTALL)

    parts = re.split(r"(?<=[.!?])\s+|\n+", answer)

    claims = []

    for part in parts:
        part = re.sub(r"^[\s\-*#\d.)]+", "", part).strip()

        if len(part) < 20:
            continue

        if re.match(
            r"^(source|sources|page|citation|reference)s?\s*:",
            part,
            flags=re.IGNORECASE
        ):
            continue

        claims.append(part)

    return claims


def verify_answer(question, answer, chunks):
    if not answer or not chunks:
        return {
            "grounded": False,
            "confidence": 0,
            "supported_claims": [],
            "unsupported_claims": [],
            "evidence_coverage": 0,
            "abstained": False
        }

    evidence = []

    for chunk in chunks:
        evidence.append({
            "page": chunk.page_number,
            "text": chunk.content,
            "tokens": _content_tokens(chunk.content)
        })

    claims = _sentence_claims(answer)

    if not claims:
        return {
            "grounded": True,
            "confidence": 1.0,
            "supported_claims": [],
            "unsupported_claims": [],
            "evidence_coverage": 1.0,
            "abstained": False
        }

    supported = []
    unsupported = []

    for claim in claims:
        claim_tokens = _content_tokens(claim)

        if not claim_tokens:
            continue

        best_score = 0
        best_page = None

        for item in evidence:
            overlap = len(claim_tokens & item["tokens"])
            score = overlap / len(claim_tokens)

            if score > best_score:
                best_score = score
                best_page = item["page"]

        claim_data = {
            "claim": claim,
            "page": best_page,
            "supported": best_score >= 0.30
        }

        if best_score >= 0.30:
            supported.append(claim_data)
        else:
            unsupported.append(claim_data)

    total = len(supported) + len(unsupported)

    if total == 0:
        confidence = 0
    else:
        confidence = len(supported) / total

    answer_lower = answer.lower()

    abstained = any(
        phrase in answer_lower
        for phrase in [
            "not provided",
            "not stated",
            "not specified",
            "not mentioned",
            "does not provide",
            "is not provided",
            "cannot be determined"
        ]
    )

    return {
        "grounded": confidence >= 0.70,
        "confidence": round(confidence, 2),
        "supported_claims": supported,
        "unsupported_claims": unsupported,
        "evidence_coverage": round(confidence, 2),
        "abstained": abstained
    }
