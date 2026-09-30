import fitz
import pytesseract
from PIL import Image
import io


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


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

        if not text:
            continue

        chunk_size = 1000

        for i in range(0, len(text), chunk_size):

            chunk = text[i:i + chunk_size].strip()

            if chunk:
                chunks.append({
                    "page_number": page_number,
                    "content": chunk
                })

    return chunks