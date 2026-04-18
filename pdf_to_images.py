import os
from pathlib import Path
from pdf2image import convert_from_path
from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "InputNotes"
OUTPUT_DIR = BASE_DIR / "PageImages"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Poppler path (adjust if needed)
POPPLER_PATH = os.environ['POPPLER_PATH']

def convert_pdf_to_images(pdf_path: Path):
    print(f"Processing: {pdf_path.name}")

    images = convert_from_path(
        pdf_path,
        dpi=300,  # important for handwriting quality
        poppler_path=POPPLER_PATH
    )

    base_name = pdf_path.stem

    saved_paths = []

    for i, img in enumerate(images):
        page_num = i + 1

        output_filename = f"{base_name}_page_{page_num}.png"
        output_path = OUTPUT_DIR / output_filename

        # Save image
        img.save(output_path, "PNG")

        saved_paths.append(output_path)
        print(f"Saved: {output_filename}")

    return saved_paths


if __name__ == "__main__":
    pdf_files = list(INPUT_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDFs found in InputNotes/")
        exit()

    # For now: process ONE file only
    pdf_path = pdf_files[0]

    convert_pdf_to_images(pdf_path)