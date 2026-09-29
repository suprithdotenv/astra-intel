import os

from dotenv import load_dotenv
from groq import Groq

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
        temperature=0
    )

    return response.choices[0].message.content