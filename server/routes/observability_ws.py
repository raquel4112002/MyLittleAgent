import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from server.state import get_event_bus

router = APIRouter()


@router.websocket("/ws/sessions/{session_id}")
async def session_events_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    bus = get_event_bus()
    queue = bus.subscribe(session_id)
    try:
        existing = bus.store.list_events(session_id)
        for item in existing:
            await websocket.send_json(item.model_dump(mode="json"))
        while True:
            event = await asyncio.wait_for(queue.get(), timeout=30.0)
            await websocket.send_json(event.model_dump(mode="json"))
    except asyncio.TimeoutError:
        await websocket.send_json({"type": "heartbeat", "session_id": session_id})
    except WebSocketDisconnect:
        pass
    finally:
        bus.unsubscribe(session_id, queue)
