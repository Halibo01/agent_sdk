# events.py
from dataclasses import dataclass
from typing import Any, Literal, Optional

EventType = Literal[
    "token",
    "reasoning",    # YENİ: Düşünme süreci için
    "tool_call",
    "tool_result",
    "final",
    "raw",
    "error"
]

@dataclass
class StreamEvent:
    type: EventType
    data: Any

    def __str__(self) -> str:
        if self.type == "raw": return ""
        # Token ve Reasoning metin tabanlıdır
        if self.type in ["token", "reasoning"]:
            return str(self.data)
        if isinstance(self.data, (dict, list)):
            return "" # JSON verisi konsolda string olarak basılmasın
        return ""

last_event_type = None
@dataclass
class AgentStreamEvent:
    type: EventType
    data: Any
    agent_name: str
    def __str__(self):
        return ""