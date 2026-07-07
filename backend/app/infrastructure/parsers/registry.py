from pathlib import Path

from app.infrastructure.parsers.docx_parser import extract_text as extract_docx_text
from app.infrastructure.parsers.pdf_parser import extract_text as extract_pdf_text
from app.infrastructure.parsers.text_parser import extract_text as extract_plain_text


SUPPORTED_TEXT_TYPES = {
    '.txt': extract_plain_text,
    '.md': extract_plain_text,
    '.pdf': extract_pdf_text,
    '.docx': extract_docx_text,
}


def normalize_extensions(extensions: list[str]) -> set[str]:
    return {item.lower() if item.startswith('.') else f'.{item.lower()}' for item in extensions}


def is_supported_document(filename: str, extensions: list[str] | None = None) -> bool:
    suffix = Path(filename or '').suffix.lower()
    allowed = normalize_extensions(extensions or list(SUPPORTED_TEXT_TYPES.keys()))
    return suffix in allowed and suffix in SUPPORTED_TEXT_TYPES


def supported_document_extensions() -> list[str]:
    return list(SUPPORTED_TEXT_TYPES.keys())


def extract_text_from_upload(filename: str, content_type: str, path: Path) -> str:
    suffix = path.suffix.lower()
    parser = SUPPORTED_TEXT_TYPES.get(suffix)
    if not parser:
        raise ValueError(f'暂不支持的文档类型: {filename or content_type}')
    return parser(path)