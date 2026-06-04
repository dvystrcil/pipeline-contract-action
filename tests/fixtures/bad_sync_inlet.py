"""Fails AC2 — inlet is `def` instead of `async def`.

Mirrors the 2026-05-09 production bug shape — sync `inlet` blocks the uvicorn
event loop on every chat turn.
"""
from pydantic import BaseModel


class Pipeline:
    class Valves(BaseModel):
        pipelines: list[str] = []

    def __init__(self) -> None:
        self.type = "filter"
        self.name = "Bad Sync Inlet"
        self.valves = self.Valves()

    async def on_startup(self) -> None:
        pass

    async def on_shutdown(self) -> None:
        pass

    async def on_valves_updated(self) -> None:
        pass

    def inlet(self, body: dict, user: dict | None = None) -> dict:
        return body
