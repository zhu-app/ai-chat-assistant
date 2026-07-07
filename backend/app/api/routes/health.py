from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=['health'])


def _path_state(path_value: str, expect_file: bool = False) -> dict[str, str | bool]:
    path = Path(path_value)
    target = path if expect_file else path.parent
    writable = target.exists() and target.is_dir()
    return {
        'path': str(path),
        'exists': path.exists(),
        'writable_parent': writable,
    }


@router.get('/health')
def health_check():
    return {'status': 'ok'}


@router.get('/health/live')
def liveness_check():
    return {'status': 'alive'}


@router.get('/health/ready')
def readiness_check():
    sqlite_state = _path_state(settings.sqlite_path, expect_file=True)
    document_store = Path(settings.document_store_dir)
    ready = sqlite_state['writable_parent'] and document_store.exists() and document_store.is_dir()
    return {
        'status': 'ready' if ready else 'degraded',
        'checks': {
            'sqlite': sqlite_state,
            'document_store': {
                'path': str(document_store),
                'exists': document_store.exists(),
                'is_dir': document_store.is_dir(),
            },
            'llm': {
                'remote_enabled': bool(settings.openai_api_key),
                'model': settings.openai_model,
            },
            'upload': {
                'max_upload_bytes': settings.max_upload_bytes,
                'allowed_extensions': settings.allowed_document_extensions,
            },
        },
    }