from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    permission_level: str
    handler: Callable[[dict], dict]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        self._tools[definition.name] = definition

    def call(self, tool_name: str, payload: dict) -> dict:
        if tool_name not in self._tools:
            raise KeyError(f"Unknown tool: {tool_name}")
        return self._tools[tool_name].handler(payload)

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())