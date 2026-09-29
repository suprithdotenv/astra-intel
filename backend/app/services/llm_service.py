import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_answer(query: str, chunks):

    context = "\n\n".join(
        [
            f"Page {chunk.page_number}:\n{chunk.content}"
            for chunk in chunks
        ]
    )

    prompt = f"""
You are ASTRA, a document intelligence assistant.

Answer the user's question using ONLY the information
provided in the document context.

If the answer is not present in the context, say:
"I could not find the answer in the provided document."

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{query}

Give a concise and accurate answer.
"""

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "system",
                    "content": "You are ASTRA, a document intelligence assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=300
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Groq API error:", e)

        return "The AI model is temporarily unavailable. Please try again."