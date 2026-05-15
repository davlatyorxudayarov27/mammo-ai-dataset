from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Optional

from fastapi import WebSocket


class RoomManager:
    def __init__(self):
        self._rooms: dict[str, set[tuple[WebSocket, str]]] = defaultdict(set)
        self._lock = asyncio.Lock()

    @staticmethod
    def room_id(source: str, ref: str) -> str:
        return f"{source}::{ref}"

    async def join(self, source: str, ref: str, ws: WebSocket, username: str):
        rid = self.room_id(source, ref)
        async with self._lock:
            self._rooms[rid].add((ws, username))
        await self.broadcast_presence(source, ref)

    async def leave(self, source: str, ref: str, ws: WebSocket, username: str):
        rid = self.room_id(source, ref)
        async with self._lock:
            self._rooms[rid].discard((ws, username))
            if not self._rooms[rid]:
                del self._rooms[rid]
        await self.broadcast_presence(source, ref)

    def members(self, source: str, ref: str) -> list[str]:
        rid = self.room_id(source, ref)
        return sorted({u for _, u in self._rooms.get(rid, set())})

    async def broadcast(
        self,
        source: str,
        ref: str,
        message: dict,
        exclude_ws: Optional[WebSocket] = None,
    ):
        rid = self.room_id(source, ref)
        recipients = list(self._rooms.get(rid, set()))
        for ws, _ in recipients:
            if ws is exclude_ws:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                pass

    async def broadcast_presence(self, source: str, ref: str):
        await self.broadcast(source, ref, {
            "type": "presence",
            "users": self.members(source, ref),
        })


rooms = RoomManager()
