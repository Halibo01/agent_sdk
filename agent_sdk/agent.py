"""
Agent Module

Defines the `Agent` class, which holds the configuration and state (identity, tools, instructions) 
for an AI assistant. The Agent is passive and is executed by a `Runner`.

Documentation: https://docs.agent-sdk-core.dev/modules/agents
"""

from typing import Optional, Dict, Callable, Any

class Agent:
    def __init__(
        self,
        name: str,
        model: str,
        instructions: str = "",
        tools: Optional[Dict[str, Callable]] = None,
        max_steps: int = 10,
        handoff_msg: Optional[str] = None,
        generation_config: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.name = name
        self.model = model
        self.instructions = instructions
        self.tools = tools or {}
        self.max_steps = max_steps
        self.handoff_msg = handoff_msg
        self.generation_config = generation_config or {}
        self.user_id = user_id
        self.session_id = session_id
        self.memory = []

    def system_prompt(self) -> str:
        base = f"You are an AI agent named {self.name}."
        if self.instructions:
            base += "\n" + self.instructions
        return base
