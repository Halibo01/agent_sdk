from .base import Middleware
import os
from typing import List, Dict, Optional

class ContextInjector(Middleware):
    def __init__(self, env_keys: Optional[List[str]] = None, static_context: Optional[Dict[str, str]] = None):
        """
        Args:
            env_keys: List of environment variable names to read from .env or system. (e.g., ['APP_ENV', 'PROJECT_ROOT'])
            static_context: Key-value pairs to inject as static context. (e.g., {'User': 'Admin', 'OS': 'Windows'})
        """
        self.env_keys = env_keys or []
        self.static_context = static_context or {}

    def before_run(self, agent, runner):
        """
        Injects context data into the agent's memory just before execution.
        """
        context_lines = []

        # 1. Read Environment Variables
        if self.env_keys:
            found_envs = False
            for key in self.env_keys:
                val = os.getenv(key)
                if val:
                    if not found_envs:
                        context_lines.append("--- Environment Context ---")
                        found_envs = True
                    context_lines.append(f"{key}: {val}")

        # 2. Add Static Data
        if self.static_context:
            context_lines.append("--- Runtime Context ---")
            for k, v in self.static_context.items():
                context_lines.append(f"{k}: {v}")

        # Exit if nothing to add
        if not context_lines:
            return

        # Create message
        injection_content = "\n".join(context_lines)
        system_note = f"\n[SYSTEM NOTICE: The following context is active for this session]\n{injection_content}\n"

        # 3. Prevent Duplication (Advanced Check)
        # If this system note is already in memory, don't add it again.
        for msg in agent.memory:
            if msg.get("role") == "system" and injection_content in msg.get("content", ""):
                return

        # Add to memory
        # We add it with the 'system' role so the agent sees it as information, not an instruction.
        agent.memory.append({
            "role": "system",
            "content": system_note
        })

        print(f"[ContextInjector] Context loaded for {agent.name}.")
