"""
Events Module

Defines the event structures used for streaming feedback from the Agent/Runner.
`AgentStreamEvent` captures tokens, tool calls, results, and reasoning steps.

Documentation: https://docs.agent-sdk-core.dev/api-reference
"""

from dataclasses import dataclass
from typing import Any, Literal, Optional

EventType = Literal[
    "token",
    "reasoning",    # NEW: For reasoning process
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
        # Token and Reasoning are text-based
        if self.type in ["token", "reasoning"]:
            return str(self.data)
        if isinstance(self.data, (dict, list)):
            return "" # Do not print JSON data as string in console
        return ""

last_event_type = None
@dataclass
class AgentStreamEvent:
    type: EventType
    data: Any
    agent_name: str
    def __str__(self):
        return ""