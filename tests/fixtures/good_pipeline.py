"""Canonical good Pipeline — passes every contract check.

Mirrors the minimum OWUI Pipeline shape: nested Valves with `pipelines: list[str]`,
async inlet + outlet + lifecycle hooks, instance attributes set in __init__.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class Pipeline:
    class Valves(BaseModel):
        pipelines: list[str] = []
        priority: int = 0

    def __init__(self) -> None:
        self.type = "filter"
        self.name = "Good Pipeline"
        self.valves = self.Valves()

    async def on_startup(self) -> None:
        pass

    async def on_shutdown(self) -> None:
        pass

    async def on_valves_updated(self) -> None:
        pass

    async def inlet(self, body: dict, user: dict | None = None) -> dict:
        return body

    async def outlet(self, body: dict, user: dict | None = None) -> dict:
        return body
