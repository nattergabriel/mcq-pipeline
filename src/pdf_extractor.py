import json
import pymupdf


def extract_pdf(path: str):
    extracted_content = []
    doc = pymupdf.open(path)
    for page_number in range(len(doc)):
        extracted_content.append({
            'page': page_number + 1,
            'text': doc[page_number].get_text()
        })
    return extracted_content


# Testing
if __name__ == "__main__":
    filename = "2025S-2-EP1-Variablen"
    extracted_content = extract_pdf(f"data/input/pdfs/{filename}.pdf")
    with open(f"data/output/extracted_content/{filename}.json", "w", encoding='utf-8') as f:
        json.dump(extracted_content, f, indent=4, ensure_ascii=False)
