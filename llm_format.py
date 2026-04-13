import os
from datetime import datetime
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
RAW_TEXT_DIR = BASE_DIR / "RawText"
MARKDOWN_DIR = BASE_DIR / "MarkdownOutput"

MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "openrouter/free"

def parse_filename_metadata(filename: str) -> dict:
    """
    Example:
    ece124_lecture05_fourier.txt
    """
    stem = Path(filename).stem
    parts = stem.split("_")

    course = ""
    lecture = ""
    topic = ""

    if len(parts) >= 1:
        course = parts[0].upper()

    if len(parts) >= 2 and parts[1].lower().startswith("lecture"):
        lecture = parts[1].replace("lecture", "").strip()

    if len(parts) >= 3:
        topic = " ".join(parts[2:]).replace("-", " ").strip().title()

    return {
        "stem": stem,
        "course": course,
        "lecture": lecture,
        "topic": topic,
    }


def build_messages(filename: str, ocr_text: str) -> tuple[str, str]:
    metadata = parse_filename_metadata(filename)
    processed_date = datetime.now().strftime("%Y-%m-%d")

    system_prompt = """You are cleaning OCR text extracted from handwritten lecture notes.

Your job is to reconstruct readable notes from noisy OCR and convert them into structured Markdown.

Process:
1. First reconstruct the OCR into the most readable plain text possible.
2. Then organize that reconstructed text into the Markdown template.

You MUST:
- Fix obvious OCR spelling errors when the intended word is reasonably clear.
- Merge broken lines into readable sentences or short paragraphs.
- Improve readability significantly.
- Preserve the original meaning as faithfully as possible.

You MUST NOT:
- Invent concepts, facts, examples, or definitions that are not supported by the OCR text.
- Add outside knowledge.
- Force nonsense fragments into fluent sentences when the meaning is unclear.

Unclear text handling:
- If a word or phrase cannot be repaired confidently, do not leave it in Content.
- Move uncertain or corrupted text into "Unclear OCR Segments".
- Be conservative, but do not leave obviously fixable OCR errors unchanged.

Title handling:
- If no reliable lecture title is present, use "Untitled Lecture".
- Do not invent placeholder titles like "LectureTitle".

Tag handling:
- Include "lecture".
- Include the course code only if it can be inferred reliably.
- Do not use meaningless filename fragments as tags.

Output requirements:
- Output only valid Markdown.
- Use clean readable prose in the Content section.
- Do not preserve raw OCR line breaks.
- Leave sections minimal if there is not enough reliable information.
"""

    user_prompt = f"""Convert the following OCR text into structured Markdown using this exact template:

# Lecture Title

**Summary**:
**Tags**:
**Created**:
**Source**:

---

## Content

## Key Ideas
-

## Definitions
-

## Examples
-

## Connections
- Related:

## Unclear OCR Segments
-

Instructions:
- First reconstruct the OCR into readable plain text.
- Then use that reconstructed text to fill the template.
- Correct obvious OCR mistakes.
- Do not hallucinate missing information.
- Do not preserve broken line structure.
- Do not leave corrupted tokens in Content if they are not reasonably recoverable.
- If a section has no reliable content, leave it minimal.

Filename: output.txt
Processed Date: 2026-04-11

OCR Text:
[paste OCR text here]
"""
    return system_prompt, user_prompt


def format_ocr_to_markdown(input_file: Path) -> Path:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    ocr_text = input_file.read_text(encoding="utf-8").strip()
    if not ocr_text:
        raise ValueError(f"OCR file is empty: {input_file}")

    system_prompt, user_prompt = build_messages(input_file.name, ocr_text)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        extra_headers={
            "HTTP-Referer": "http://localhost",
            "X-OpenRouter-Title": "Notes Wiki",
        },
    )

    markdown = response.choices[0].message.content.strip()

    output_file = MARKDOWN_DIR / f"{input_file.stem}.md"
    output_file.write_text(markdown, encoding="utf-8")

    return output_file


if __name__ == "__main__":
    input_filename = "output.txt"  # change if needed
    input_path = RAW_TEXT_DIR / input_filename

    output_path = format_ocr_to_markdown(input_path)
    print(f"Markdown saved to: {output_path}")