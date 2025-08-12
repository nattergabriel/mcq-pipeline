from src.pdf_extractor import extract_pdf
from src.mcqs_generator import generate_mcqs
from src.mcqs_reviewer import review_mcqs
from src.moodle_exporter import export_mcqs


def main():
    extracted_text = extract_pdf("data/input/pdfs/2025S-2-EP1-Variablen.pdf")
    mcqs = generate_mcqs(extracted_text)
    reviewed_mcqs = review_mcqs(mcqs)
    export_mcqs(reviewed_mcqs)


if __name__ == "__main__":
    main()
