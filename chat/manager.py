from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[int, dict[str, WebSocket]] = {}
        self.user_connections: dict[str, tuple[int, str, WebSocket]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        room_id: int,
        role: str,
        user_id: str,
        is_staff: bool,
    ) -> None:
        if not is_staff and user_id in self.user_connections:
            old_room_id, old_role, old_ws = self.user_connections[user_id]
            try:
                await old_ws.close(code=4009, reason="session replaced")
            except Exception:
                pass
            old_room = self.rooms.get(old_room_id)
            if old_room:
                if old_room.get(old_role) is old_ws:
                    del old_room[old_role]
                if not old_room:
                    del self.rooms[old_room_id]

        await websocket.accept()
        self.rooms.setdefault(room_id, {})[role] = websocket

        if not is_staff:
            self.user_connections[user_id] = (room_id, role, websocket)

    def disconnect(
        self, room_id: int, role: str, user_id: str, is_staff: bool
    ) -> None:
        room = self.rooms.get(room_id)
        if room:
            room.pop(role, None)
            if not room:
                del self.rooms[room_id]

        if not is_staff:
            self.user_connections.pop(user_id, None)

    def get_peer(self, room_id: int, sender_role: str) -> WebSocket | None:
        peer_role = "agent" if sender_role == "user" else "user"
        room = self.rooms.get(room_id)
        return room.get(peer_role) if room else None


manager = ConnectionManager()
