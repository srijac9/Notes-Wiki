import os
import re
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
PAGE_NOTES_DIR = BASE_DIR / "PageNotes"
MARKDOWN_OUTPUT_DIR = Path(r"C:\Users\srich\OneDrive\Documents\Notes-Wiki\Lectures")

MARKDOWN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "openrouter/free"

def extract_base_and_page(filename: str) -> tuple[str, int]:
    """
    Example:
    ece119_lecture1_page_2.md
    -> ("ece119_lecture1", 2)
    """
    match = re.match(r"^(.*)_page_(\d+)\.md$", filename)
    if not match:
        raise ValueError(f"Filename does not match expected format: {filename}")
    base_name = match.group(1)
    page_num = int(match.group(2))
    return base_name, page_num


def group_page_notes() -> dict[str, list[Path]]:
    grouped: dict[str, list[tuple[int, Path]]] = {}

    for path in PAGE_NOTES_DIR.glob("*.md"):
        try:
            base_name, page_num = extract_base_and_page(path.name)
        except ValueError:
            continue

        grouped.setdefault(base_name, []).append((page_num, path))

    sorted_grouped: dict[str, list[Path]] = {}
    for base_name, items in grouped.items():
        items.sort(key=lambda x: x[0])
        sorted_grouped[base_name] = [path for _, path in items]

    return sorted_grouped


def build_merge_input(page_files: list[Path]) -> str:
    chunks = []

    for path in page_files:
        page_text = path.read_text(encoding="utf-8").strip()
        chunks.append(f"--- BEGIN {path.name} ---\n{page_text}\n--- END {path.name} ---")

    return "\n\n".join(chunks)


def parse_filename_metadata(base_name: str) -> dict:
    """
    Example:
    ece119_lecture1
    ece119_lecture1_limits
    """
    parts = base_name.split("_")

    course = ""
    lecture = ""
    topic = ""

    if len(parts) >= 1:
        course = parts[0].upper()

    for part in parts[1:]:
        if part.lower().startswith("lecture"):
            lecture = part.replace("lecture", "").strip()
            break

    non_topic_parts = {parts[0].lower()}
    if lecture:
        non_topic_parts.add(f"lecture{lecture}".lower())

    topic_parts = [p for p in parts[1:] if p.lower() not in non_topic_parts and not p.lower().startswith("lecture")]
    if topic_parts:
        topic = " ".join(topic_parts).replace("-", " ").title()

    return {
        "course": course,
        "lecture": lecture,
        "topic": topic,
    }


def build_prompts(base_name: str, combined_page_notes: str) -> tuple[str, str]:
    metadata = parse_filename_metadata(base_name)
    processed_date = datetime.now().strftime("%Y-%m-%d")

    system_prompt = """You are merging page-level extractions from handwritten lecture notes into one structured Markdown wiki note.

Your job is to create a clean, searchable, faithful lecture note for an LLM knowledge base.

You MUST:
- Merge duplicate information across pages.
- Preserve mathematical notation and equations when readable.
- Preserve important headings and topic structure when supported by the page notes.
- Summarize clearly and conservatively.
- Keep diagrams as short text descriptions rather than trying to redraw them.

You MUST NOT:
- Invent facts, equations, definitions, or examples that are not supported by the page notes.
- Add outside knowledge.
- Present unclear material as certain.

Handling unclear content:
- Move ambiguous or corrupted items into 'Unclear OCR / Vision Segments'.
- Keep the main content clean and readable.

Title handling:
- If the lecture title is clear from the page notes, use it.
- Otherwise use a cautious fallback based on the filename, or 'Untitled Lecture'.

Output only valid Markdown.
"""

    user_prompt = f"""Combine the following page-level lecture note extractions into one structured Markdown note.

Use this exact template:

# Lecture Title

**Summary**:
**Tags**:
**Created**:
**Source**:

---

## Main Concepts
-

## Key Equations
-

## Examples
-

## Diagrams / Figures
-

## Connections
- Related:

## Unclear OCR / Vision Segments
-

Instructions:
- Merge repeated content across pages.
- Keep the result concise and readable.
- Preserve equations when readable.
- If examples are present, list them briefly.
- If diagrams are present, summarize them briefly.
- Tags should include "lecture" and the course code if reliable.
- Source should be the original base filename with .pdf.
- Do not include page-by-page sections in the final note.
- Do not hallucinate missing information.

Filename base: {base_name}
Course: {metadata["course"] or "Unknown"}
Lecture: {metadata["lecture"] or "Unknown"}
Topic hint: {metadata["topic"] or "Unknown"}
Processed Date: {processed_date}

Page note inputs:
{combined_page_notes}
"""
    return system_prompt, user_prompt


def merge_one_lecture(base_name: str, page_files: list[Path]) -> Path:
    combined_page_notes = build_merge_input(page_files)
    system_prompt, user_prompt = build_prompts(base_name, combined_page_notes)

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

    output_path = MARKDOWN_OUTPUT_DIR / f"{base_name}.md"
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def main() -> None:
    grouped = group_page_notes()

    if not grouped:
        print("No page note files found in PageNotes/")
        return

    print(f"Found {len(grouped)} lecture group(s).")

    for base_name, page_files in grouped.items():
        print(f"Merging {len(page_files)} page note(s) for: {base_name}")
        try:
            output_path = merge_one_lecture(base_name, page_files)
            print(f"Saved merged note: {output_path.name}")
        except Exception as e:
            print(f"Failed to merge {base_name}: {e}")


if __name__ == "__main__":
    main()