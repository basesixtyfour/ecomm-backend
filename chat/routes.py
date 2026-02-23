import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from auth import verify_token
from database import AsyncSessionLocal
from manager import manager
from models import ChatRoom, ChatRoomStatus

router = APIRouter()


async def _send_json(ws: WebSocket, payload: dict) -> None:
    try:
        await ws.send_text(json.dumps(payload))
    except Exception:
        pass


@router.websocket("/ws/support/{room_id}")
async def support_ws(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(...),
):
    claims = verify_token(token)
    if not claims:
        await websocket.close(code=4001, reason="invalid token")
        return

    user_id: str = claims["user_id"]
    is_staff: bool = claims["is_staff"]

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ChatRoom).where(ChatRoom.id == room_id)
        )
        room = result.scalar_one_or_none()

        if not room:
            await websocket.close(code=4004, reason="room not found")
            return

        if room.status == ChatRoomStatus.closed:
            await websocket.close(code=4003, reason="room closed")
            return

        if is_staff:
            role = "agent"
            if not room.agent_id:
                room.agent_id = user_id
                await session.commit()
        elif user_id == room.user_id:
            role = "user"
        else:
            await websocket.close(code=4003, reason="not a participant")
            return

    await manager.connect(websocket, room_id, role, user_id, is_staff)

    peer = manager.get_peer(room_id, role)
    if peer:
        await _send_json(peer, {
            "type": "presence",
            "sender_role": role,
            "status": "online",
        })

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await _send_json(websocket, {
                    "type": "error",
                    "content": "invalid JSON",
                })
                continue

            msg_type = data.get("type")

            if msg_type == "message":
                content = data.get("content", "").strip()
                if not content:
                    continue

                peer = manager.get_peer(room_id, role)
                if peer:
                    await _send_json(peer, {
                        "type": "message",
                        "sender_role": role,
                        "content": content,
                    })
                else:
                    await _send_json(websocket, {
                        "type": "system",
                        "content": "the other party is not connected",
                    })

            elif msg_type == "typing":
                peer = manager.get_peer(room_id, role)
                if peer:
                    await _send_json(peer, {
                        "type": "typing",
                        "sender_role": role,
                        "is_typing": bool(data.get("is_typing", True)),
                    })

    except WebSocketDisconnect:
        manager.disconnect(room_id, role, user_id, is_staff)
        peer = manager.get_peer(room_id, role)
        if peer:
            await _send_json(peer, {
                "type": "presence",
                "sender_role": role,
                "status": "offline",
            })
