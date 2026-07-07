from typing import AsyncIterator


def sse_event(payload: dict) -> str:
    import json
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def event_stream(events: AsyncIterator[dict]):
    async for event in events:
        yield sse_event(event)