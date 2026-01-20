from .base import Middleware
import json
import datetime
import os
import asyncio

class FileLogger(Middleware):
    def __init__(self, filename: str = "agent_activity.jsonl"):
        self.filename = filename
        # Dosya yoksa oluştur
        if not os.path.exists(self.filename):
            with open(self.filename, "w", encoding="utf-8") as f:
                pass

    def _log(self, data: dict):
        """Senkron loglama (bloklar)"""
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def before_tool_execution(self, agent, runner, tool_name, tool_args, tool_call_id=None) -> bool:
        """Tool kullanımını logla (Sync)"""
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
        """Ajanın son durumunu logla (Sync)"""
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
        """Tool kullanımını logla (Async - Non-blocking)"""
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "tool_attempt",
            "agent": agent.name,
            "tool": tool_name,
            "args": tool_args,
            "call_id": tool_call_id
        }
        # Dosya yazma işlemini thread'de yap, loop'u bloklama
        await asyncio.to_thread(self._log, entry)
        return True

    async def after_run_async(self, agent, runner):
        """Ajanın son durumunu logla (Async - Non-blocking)"""
        if agent.memory:
            last_msg = agent.memory[-1]
            entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "run_complete",
                "agent": agent.name,
                "last_message": last_msg
            }
            await asyncio.to_thread(self._log, entry)
