from .base import Middleware
import json
import datetime
import os
import asyncio

class FileLogger(Middleware):
    def __init__(self, filename: str = "agent_activity.jsonl"):
        self.filename = filename
        # Create file if it doesn't exist
        if not os.path.exists(self.filename):
            with open(self.filename, "w", encoding="utf-8") as f:
                pass

    def _log(self, data: dict):
        """Synchronous logging (blocking)"""
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def before_tool_execution(self, agent, runner, tool_name, tool_args, tool_call_id=None) -> bool:
        """Log tool usage (Sync)"""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "tool_attempt",
            "agent": agent.name,
            "tool": tool_name,
            "args": tool_args,
            "call_id": tool_call_id
        }
        self._log(entry)
        return True

    def after_run(self, agent, runner):
        """Log agent's final state (Sync)"""
        if agent.memory:
            last_msg = agent.memory[-1]
            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "run_complete",
                "agent": agent.name,
                "last_message": last_msg
            }
            self._log(entry)

    # --- ASYNC METHODS ---

    async def before_tool_execution_async(self, agent, runner, tool_name: str, tool_args: dict, tool_call_id: str = None) -> bool:
        """Log tool usage (Async - Non-blocking)"""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "tool_attempt",
            "agent": agent.name,
            "tool": tool_name,
            "args": tool_args,
            "call_id": tool_call_id
        }
        # Write to file in thread, do not block loop
        await asyncio.to_thread(self._log, entry)
        return True

    async def after_run_async(self, agent, runner):
        """Log agent's final state (Async - Non-blocking)"""
        if agent.memory:
            last_msg = agent.memory[-1]
            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "run_complete",
                "agent": agent.name,
                "last_message": last_msg
            }
            await asyncio.to_thread(self._log, entry)
