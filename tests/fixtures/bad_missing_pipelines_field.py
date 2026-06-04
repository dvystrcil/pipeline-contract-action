"""Fails AC4 — Valves is missing the `pipelines: list[str]` field.

Mirrors the 2026-05-08 production bug — pipelines disappear from the OWUI
admin UI because the Pipelines runtime can't enumerate them without this field.
"""
from pydantic import BaseModel


class Pipeline:
    class Valves(BaseModel):
        priority: int = 0
        # missing: pipelines: list[str] = []

    def __init__(self) -> None:
        self.type = "filter"
        self.name = "Bad Missing Pipelines Field"
        self.valves = self.Valves()

    async def on_startup(self) -> None:
        pass

    async def inlet(self, body: dict, user: dict | None = None) -> dict:
        return body
