import base64
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in .env")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

BASE_DIR = Path(__file__).resolve().parent
PAGE_IMAGES_DIR = BASE_DIR / "PageImages"
PAGE_NOTES_DIR = BASE_DIR / "PageNotes"
FAILED_DIR = BASE_DIR / "Failed"

PAGE_NOTES_DIR.mkdir(parents=True, exist_ok=True)
FAILED_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "openrouter/free"
REQUEST_DELAY_SECONDS = 3.5  # helps avoid free-tier rate issues


def encode_image_to_data_url(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    if suffix == ".png":
        media_type = "image/png"
    elif suffix in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif suffix == ".webp":
        media_type = "image/webp"
    else:
        raise ValueError(f"Unsupported image type: {suffix}")

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{media_type};base64,{encoded}"


def build_prompt(page_name: str) -> str:
    return f"""Read this handwritten lecture note page and extract it conservatively.

Return markdown with exactly these sections:

## Page

### Readable Text
- Transcribe readable handwritten content into clean sentences or bullets.
- Preserve headings when visible.
- If a statement is mathematically inconsistent, prefer the visually supported interpretation from the page when reasonably clear.

### Equations
- List equations and formulas exactly when readable.
- For definitions and notation, prioritize mathematical correctness when the handwriting is clear enough to support it.
- If unclear, move them to Unclear Items instead of guessing.

### Diagrams / Figures
- Briefly describe any graph, sketch, surface, labeled figure, or geometric drawing.

### Unclear Items
- List unreadable or ambiguous words, symbols, and formulas.

Rules:
- Do not invent missing content.
- Do not use outside knowledge.
- Preserve math notation when possible.
- Be concise and faithful to the page.
- If the page is blank or nearly blank, say so clearly.
- Do not include any section other than the four sections above.

Page filename: {page_name}
"""


def process_one_page(image_path: Path) -> Path:
    image_data_url = encode_image_to_data_url(image_path)
    prompt = build_prompt(image_path.name)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url},
                    },
                ],
            }
        ],
        temperature=0.1,
        extra_headers={
            "HTTP-Referer": "http://localhost",
            "X-OpenRouter-Title": "Notes Wiki",
        },
    )

    content = response.choices[0].message.content.strip()
    output_path = PAGE_NOTES_DIR / f"{image_path.stem}.md"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def log_failure(image_path: Path, error: Exception) -> None:
    error_file = FAILED_DIR / f"{image_path.stem}_error.txt"
    error_file.write_text(str(error), encoding="utf-8")


def main() -> None:
    image_files = sorted(
        [
            p for p in PAGE_IMAGES_DIR.iterdir()
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        ]
    )

    if not image_files:
        print("No page images found in PageImages/")
        return

    print(f"Found {len(image_files)} page image(s).")

    for index, image_path in enumerate(image_files, start=1):
        output_path = PAGE_NOTES_DIR / f"{image_path.stem}.md"

        if output_path.exists():
            print(f"[{index}/{len(image_files)}] Skipping existing: {output_path.name}")
            continue

        print(f"[{index}/{len(image_files)}] Processing: {image_path.name}")

        try:
            saved_path = process_one_page(image_path)
            print(f"Saved: {saved_path.name}")
        except Exception as e:
            print(f"Failed: {image_path.name} -> {e}")
            log_failure(image_path, e)

        # free-tier friendly pacing
        if index < len(image_files):
            time.sleep(REQUEST_DELAY_SECONDS)


if __name__ == "__main__":
    main()