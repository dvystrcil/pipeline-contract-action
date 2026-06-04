"""Fails AC5 — __init__ doesn't set the required type/name/valves attributes."""
from pydantic import BaseModel


class Pipeline:
    class Valves(BaseModel):
        pipelines: list[str] = []

    def __init__(self) -> None:
        # missing: self.type, self.name, self.valves
        pass

    async def on_startup(self) -> None:
        pass

    async def inlet(self, body: dict, user: dict | None = None) -> dict:
        return body
