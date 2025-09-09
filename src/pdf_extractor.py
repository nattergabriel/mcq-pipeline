import json
import pymupdf
from pathlib import Path
from typing import List, Dict, Any


def extract_text_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    extracted_content = []
    try:
        doc = pymupdf.open(pdf_path)
        for page_number in range(len(doc)):
            blocks = doc[page_number].get_text("blocks")
            page_text_blocks = [block[4] for block in blocks]
            extracted_content.append({
                'page': page_number + 1,
                'text_blocks': page_text_blocks
            })
        return extracted_content
    except Exception as e:
        print(f"Failed to process {pdf_path.name}: {e}")
        return []


def main():
    input_dir = Path("data/input/pdfs")
    output_dir = Path("data/output/extracted_content")
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in '{input_dir}'.")
        return
    for pdf_path in pdf_files:
        content = extract_text_from_pdf(pdf_path)
        if content:
            output_path = output_dir / (pdf_path.stem + ".json")
            try:
                with open(output_path, "w", encoding='utf-8') as f:
                    json.dump(content, f, indent=4, ensure_ascii=False)
            except IOError as e:
                print(f"Could not write to file '{output_path}': {e}")


if __name__ == "__main__":
    main()
