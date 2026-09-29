import  fitz

def extract_chunks(file_path:str):

    document = fitz.open(file_path)

    chunks = []

    for page_number,page in enumerate(document,start=1):

        text = page.get_text("text").strip()


        if not text:
            continue


        chunk_size = 1000

        for i in range(0,len(text),chunk_size):

            chunk = text[i:i+chunk_size].strip()

            if chunk:
                chunks.append({
                    "page_number":page_number,
                    "content":chunk,
                })


    return chunks






