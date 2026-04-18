# My Notes Wiki

> [Inspired by Andrej Karpathy’s idea of an LLM-powered personal wiki](https://www.mindstudio.ai/blog/andrej-karpathy-llm-wiki-knowledge-base-claude-code) 

---

## Overview

Notes Wiki is a project I made so I don’t have to flip through pages of handwritten notes every time I need to find one thing or answer a simple question.

I built this for my 2B term at the University of Waterloo to keep track of course material and quickly find information without manually flipping through notes. The system converts handwritten notes into structured, searchable data and allows me to query them using an LLM.

--- 

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenRouter](https://img.shields.io/badge/OpenRouter-5A67D8?style=for-the-badge)
![OCR + Parsing](https://img.shields.io/badge/Note%20Extraction-4CAF50?style=for-the-badge)

---

## The Pipeline

| File | Description |
|------|------------|
| `receiver.py` | Uploads handwritten notes (PDFs) from my iPad into `/data/input_notes` |
| `pdf_to_images.py` | Converts PDFs into individual page images → `/data/page_images` |
| `vision_all_pages.py` | Uses a vision-capable LLM to read each page and extract raw notes → `/data/page_notes` |
| `llm_format.py` | Cleans and standardizes the extracted notes into a consistent structure → `/data/page_notes` |
| `merge_notes.py` | Combines formatted page notes into larger, cohesive documents → Obsidian Notes Folder |

---

## How It Works

```text
iPad Notes (PDF)
    ↓
receiver.py
    ↓
pdf_to_images.py
    ↓
vision_all_pages.py
    ↓
llm_format.py
    ↓
merge_notes.py
    ↓
Structured Notes → Obsidian + LLM querying
```
## Quick Start

### 1. Set up iPad upload shortcut

- Create a shortcut on your iPad that:
  - Exports your handwritten notes as a **PDF**
  - Sends the file to your local computer server using your computer’s IP address

- Configure the shortcut to:
  - Use a **POST request** to your computer’s IP (e.g. `http://<your-ip>:<port>/upload`)
  - Attach the PDF as a file in the request

This lets you send notes directly from your iPad into the project in one tap. Or simply airdrop if you're using a Mac. 

### 2. Start the receiver

```bash
python reciever.py
```

- This listens for incoming PDFs from your iPad
- Use the shortcut to export your files
- Files are saved into:
  ```
  /InputNotes
  ```

---

### 3. Process notes into images

```bash
python pdf_to_images.py
```

- Converts each PDF into individual page images
- Output:
  ```
  /PageImages
  ```

---

### 4. Extract notes using LLM

```bash
python vision_all_pages.py
```

- Uses a vision-capable LLM to read each page
- Outputs raw extracted notes:
  ```
  /PageNotes
  ```

---

### 5. Clean + format notes

```bash
python llm_format.py
```

- Standardizes and cleans LLM output
- Keeps everything consistent for later use

---

### 6. Merge notes

```bash
python merge_notes.py
```

- Combines page-level notes into full documents

---

### 7. Use in Obsidian

- Move or sync the final notes into your Obsidian vault
- Use Claude (or another LLM) to:
  - Search your notes
  - Ask questions
  - Explore concepts

---

