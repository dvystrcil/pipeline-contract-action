"""Fails AC3 — on_startup is `def` instead of `async def`."""
from pydantic import BaseModel


class Pipeline:
    class Valves(BaseModel):
        pipelines: list[str] = []

    def __init__(self) -> None:
        self.type = "filter"
        self.name = "Bad Sync Lifecycle"
        self.valves = self.Valves()

    def on_startup(self) -> None:
        pass

    async def on_shutdown(self) -> None:
        pass

    async def inlet(self, body: dict, user: dict | None = None) -> dict:
        return body
