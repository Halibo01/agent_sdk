from .base import Middleware
import sqlite3
import json
import datetime
import os
import asyncio
from typing import Optional

class SQLiteLogger(Middleware):
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the database and table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple and flexible log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                agent_name TEXT,
                event_type TEXT, -- 'run_start', 'tool_use', 'message', 'error'
                summary TEXT,    -- Short summary or message content
                details JSON     -- All parameters and details
            )
        """)
        conn.commit()
        conn.close()

    def _insert_log(self, agent_name: str, event_type: str, summary: str, details: dict):
        """Synchronous log insertion"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO activity_logs (timestamp, agent_name, event_type, summary, details)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.datetime.now().isoformat(),
                agent_name,
                event_type,
                summary,
                json.dumps(details, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SQLiteLogger] Error: {e}")

    # --- SYNCHRONOUS HOOKS ---

    def before_run(self, agent, runner):
        # When agent starts running
        # Find last user message (usually the last added one)
        last_msg = agent.memory[-1] if agent.memory else {}
        task_preview = last_msg.get("content", "")[:100] if last_msg.get("role") == "user" else "Continuing..."
        
        self._insert_log(
            agent_name=agent.name,
            event_type="run_start",
            summary=f"Task started: {task_preview}",
            details={"memory_size": len(agent.memory)}
        )

    def before_tool_execution(self, agent, runner, tool_name: str, tool_args: dict) -> bool:
        self._insert_log(
            agent_name=agent.name,
            event_type="tool_use",
            summary=f"Calling {tool_name}",
            details={"tool": tool_name, "args": tool_args}
        )
        return True

    def after_run(self, agent, runner):
        # Save agent's last response
        last_msg = agent.memory[-1] if agent.memory else {}
        content = last_msg.get("content") or ""
        
        self._insert_log(
            agent_name=agent.name,
            event_type="run_complete",
            summary=content[:100] + "...",
            details=last_msg
        )

    # --- ASYNCHRONOUS HOOKS ---

    async def before_run_async(self, agent, runner):
        # Save in thread for async mode
        last_msg = agent.memory[-1] if agent.memory else {}
        task_preview = last_msg.get("content", "")[:100] if last_msg.get("role") == "user" else "Continuing..."
        
        await asyncio.to_thread(
            self._insert_log, 
            agent.name, "run_start", f"Task started: {task_preview}", {"memory_size": len(agent.memory)}
        )

    async def before_tool_execution_async(self, agent, runner, tool_name: str, tool_args: dict) -> bool:
        await asyncio.to_thread(
            self._insert_log,
            agent.name, "tool_use", f"Calling {tool_name}", {"tool": tool_name, "args": tool_args}
        )
        return True

    async def after_run_async(self, agent, runner):
        last_msg = agent.memory[-1] if agent.memory else {}
        content = last_msg.get("content") or ""
        
        await asyncio.to_thread(
            self._insert_log,
            agent.name, "run_complete", content[:100] + "...", last_msg
        )