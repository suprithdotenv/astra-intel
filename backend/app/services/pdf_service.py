import fitz
import pytesseract
from PIL import Image
import io
import re

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def clean_text(text: str):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_chunks(file_path: str):

    document = fitz.open(file_path)

    chunks = []

    for page_number, page in enumerate(document, start=1):

        text = page.get_text("text").strip()

        if not text:

            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

            image_bytes = pix.tobytes("png")

            image = Image.open(io.BytesIO(image_bytes))

            text = pytesseract.image_to_string(image).strip()

        text = clean_text(text)

        if not text:
            continue

        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""

        for sentence in sentences:

            if len(current_chunk) + len(sentence) <= 1200:
                current_chunk += " " + sentence

            else:

                if current_chunk.strip():
                    chunks.append({
                        "page_number": page_number,
                        "content": current_chunk.strip()
                    })

                current_chunk = sentence

        if current_chunk.strip():
            chunks.append({
                "page_number": page_number,
                "content": current_chunk.strip()
            })

    return chunks