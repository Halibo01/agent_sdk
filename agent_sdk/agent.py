# agent.py
from typing import Optional, Dict, Callable

class Agent:
    def __init__(
        self,
        name: str,
        model: str,
        instructions: str = "",
        tools: Optional[Dict[str, Callable]] = None,
        max_steps: int = 10,
        handoff_msg: Optional[str] = None,
        client_type: Optional[str] = None, # New parameter
        api_key: Optional[str] = None,      # New parameter
        mode: str = "sync"                 # New parameter: 'sync' or 'async'
    ):
        self.name = name
        self.model = model
        self.instructions = instructions
        self.tools = tools or {}
        self.max_steps = max_steps
        self.handoff_msg = handoff_msg
        self.client_type = client_type # Store new parameter
        self.api_key = api_key         # Store new parameter
        self.mode = mode               # Store mode
        self.memory = []

    def system_prompt(self) -> str:
        base = f"You are an AI agent named {self.name}."
        if self.instructions:
            base += "\n" + self.instructions
        return base
