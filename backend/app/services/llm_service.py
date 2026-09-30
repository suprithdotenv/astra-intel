import os

from dotenv import load_dotenv
from groq import Groq
import json

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_answer(question: str, chunks, previous_messages=None):

    context = "\n\n".join(
        f"[Page {chunk.page_number}]\n{chunk.content}"
        for chunk in chunks
    )

    history = ""

    if previous_messages:
        history = "\n".join(
            f"User: {m.question}\nAssistant: {m.answer}"
            for m in previous_messages[-5:]
        )

    prompt = f"""
You are ASTRA, a document intelligence assistant.

Answer ONLY using the provided document context.

Previous conversation:
{history}

Document context:
{context}

Current question:
{question}

If the answer is not supported by the document, say:
"I couldn't find this information in the provided document."

Cite the relevant page numbers.
"""

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=800
    )

    return response.choices[0].message.content




def compare_documents(document1_name, document2_name, chunks1, chunks2):

    context1 = "\n\n".join(
        f"[Page {chunk.page_number}]\n{chunk.content}"
        for chunk in chunks1
    )

    context2 = "\n\n".join(
        f"[Page {chunk.page_number}]\n{chunk.content}"
        for chunk in chunks2
    )

    prompt = f"""
You are ASTRA, a document intelligence assistant.

Compare the following two documents using ONLY the provided content.

DOCUMENT 1: {document1_name}
{context1}

DOCUMENT 2: {document2_name}
{context2}

Provide:

1. Main topic of each document
2. Key points of Document 1
3. Key points of Document 2
4. Similarities
5. Differences

Do not add information that is not present in the documents.
Mention relevant page numbers when possible.
"""

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=800
    )

    return response.choices[0].message.content




def verify_answer(question, answer, chunks):
    context = "\n\n".join(
        f"[Page {chunk.page_number}]\n{chunk.content}"
        for chunk in chunks
    )

    prompt = f"""
You are ASTRA's evidence verification system.

Verify whether the answer is fully supported by the provided document evidence.

Question:
{question}

Answer:
{answer}

Evidence:
{context}

Return ONLY valid JSON in this exact format:
{{
  "grounded": true,
  "confidence": 0.0,
  "supported_claims": [
    {{
      "claim": "claim from answer",
      "page": 1,
      "supported": true
    }}
  ],
  "unsupported_claims": []
}}

confidence must be between 0 and 1.
If a claim is not supported by the evidence, mark it unsupported.
"""

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=800
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "grounded": False,
            "confidence": 0,
            "supported_claims": [],
            "unsupported_claims": []
        }
