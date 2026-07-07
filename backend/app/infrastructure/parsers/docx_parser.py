from pathlib import Path

from docx import Document


def extract_text(path: Path) -> str:
    document = Document(str(path))
    return '\n'.join(paragraph.text for paragraph in document.paragraphs).strip()