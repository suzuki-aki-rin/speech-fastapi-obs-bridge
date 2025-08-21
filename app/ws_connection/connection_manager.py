from fastapi import WebSocket
from typing import Dict


class WsConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    def add(self, client_id: str, websocket: WebSocket):
        self.active_connections[client_id] = websocket

    def remove(self, client_id: str):
        self.active_connections.pop(client_id, None)

    def get(self, client_id: str) -> WebSocket | None:
        return self.active_connections.get(client_id)

    def is_connected(self, client_id: str) -> bool:
        ws = self.get(client_id)
        return ws is not None and ws.client_state.name == "CONNECTED"
