import sqlite3
import json
import asyncio
import datetime
from typing import Optional, List, Dict
from .base import Middleware

class EngramMiddleware(Middleware):
    """
    Cognitive Memory Middleware (Episodic Memory).
    Unlike standard RAG which blindly saves raw text, this middleware acts as the agent's 'Hippocampus'.
    It analyzes every interaction, extracts core facts or events (Engrams), scores their importance (1-10),
    and only saves highly important memories with a timestamp.
    """

    HEADER = "CORE MEMORIES (Engrams):"

    def __init__(self, db_path: str = "agent_engrams.db", importance_threshold: int = 5, extraction_model: str = None,
                 recall_limit: int = 5):
        """
        Initializes the EngramMiddleware.

        Args:
            db_path (str): Path to the SQLite database file. Defaults to "agent_engrams.db".
            importance_threshold (int): Minimum importance score (1-10) to save a memory. Defaults to 5.
            extraction_model (str): Model to use for engram extraction. If None, uses the agent's model.
            recall_limit (int): Max number of engrams to retrieve and inject. Defaults to 5.
        """
        self.db_path = db_path
        self.importance_threshold = importance_threshold
        self.extraction_model = extraction_model
        self.recall_limit = recall_limit
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS engrams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                agent_name TEXT,
                user_id TEXT,
                memory_trace TEXT,
                importance INTEGER
            )
        ''')
        try:
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS engrams_search USING fts5(
                    memory_trace, content='engrams', content_rowid='id'
                )
            ''')
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()

    def _extract_engram(self, runner, agent, user_text: str, agent_text: str) -> Optional[Dict]:
        """Uses a fast LLM call to evaluate the interaction and extract a memory trace."""
        prompt = f"""
Analyze the following interaction between a User and an AI Agent.
Extract any permanent, important facts, preferences, or events that the agent should remember forever.
Score the importance of this fact from 1 to 10. (1=trivial chat, 10=critical user data/preference/event).
If there is nothing worth remembering, return importance 0.

User: {user_text}
Agent: {agent_text}

Respond STRICTLY in JSON format:
{{"fact": "Extracted memory trace here (or empty)", "importance": 8}}
"""
        try:
            messages = [{"role": "user", "content": prompt}]
            model = self.extraction_model or agent.model
            response = runner.client.chat(model=model, messages=messages, temperature=0.0)
            content = response["content"].strip()

            # Clean markdown code blocks if present
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]

            data = json.loads(content.strip())
            return data
        except Exception as e:
            print(f"[Engram] Extraction error: {e}")
            return None

    async def _extract_engram_async(self, runner, agent, user_text: str, agent_text: str) -> Optional[Dict]:
        """Async version of engram extraction."""
        prompt = f"""
Analyze the following interaction between a User and an AI Agent.
Extract any permanent, important facts, preferences, or events that the agent should remember forever.
Score the importance of this fact from 1 to 10. (1=trivial chat, 10=critical user data/preference/event).
If there is nothing worth remembering, return importance 0.

User: {user_text}
Agent: {agent_text}

Respond STRICTLY in JSON format:
{{"fact": "Extracted memory trace here (or empty)", "importance": 8}}
"""
        try:
            messages = [{"role": "user", "content": prompt}]
            model = self.extraction_model or agent.model
            response = await runner.client.chat_async(model=model, messages=messages, temperature=0.0)
            content = response["content"].strip()

            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]

            data = json.loads(content.strip())
            return data
        except Exception as e:
            print(f"[Engram] Async extraction error: {e}")
            return None

    def _save_engram(self, agent_name: str, user_id: str, fact: str, importance: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()

        cursor.execute(
            "INSERT INTO engrams (timestamp, agent_name, user_id, memory_trace, importance) VALUES (?, ?, ?, ?, ?)",
            (now, agent_name, user_id or "global", fact, importance)
        )
        row_id = cursor.lastrowid
        try:
            cursor.execute(
                "INSERT INTO engrams_search (rowid, memory_trace) VALUES (?, ?)",
                (row_id, fact)
            )
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        print(f"[Engram] Memory formed (Importance {importance}/10): {fact}")

    def _retrieve_engrams(self, user_id: str, limit: int = 5) -> List[tuple]:
        """Retrieves the most important/recent engrams for a user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, importance, memory_trace
            FROM engrams
            WHERE user_id = ? OR user_id = 'global'
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        ''', (user_id or "global", limit))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def _build_engram_text(self, rows: List[tuple]) -> str:
        """Builds the engram context string from database rows."""
        text = f"{self.HEADER}\n"
        for row in rows:
            time_str = datetime.datetime.fromisoformat(row[0]).strftime("%Y-%m-%d %H:%M")
            text += f"[{time_str}] (Importance: {row[1]}/10) {row[2]}\n"
        return text

    def _cleanup_context(self, agent):
        """Removes Engram-injected messages from agent memory to prevent bloat."""
        if not agent.memory: return
        for i in range(len(agent.memory) - 1, -1, -1):
            msg = agent.memory[i]
            if msg.get("role") == "system" and msg.get("content", "").startswith(self.HEADER):
                agent.memory.pop(i)

    # --- SYNC HOOKS ---
    def before_run(self, agent, runner):
        """Retrieve recent or highly important Engrams before the agent acts."""
        user_id = getattr(agent, "user_id", None)
        rows = self._retrieve_engrams(user_id, limit=self.recall_limit)

        if rows:
            engram_text = self._build_engram_text(rows)
            print(f"[Engram] {len(rows)} core memories injected.")
            # Inject before the last user message (same pattern as SimpleRAG/ChromaRAG)
            agent.memory.insert(len(agent.memory) - 1, {
                "role": "system",
                "content": engram_text
            })

    def after_run(self, agent, runner):
        """After interaction, form a new Engram."""
        # Find the last user and assistant messages safely (handles tool calls in between)
        user_msg = next((m["content"] for m in reversed(agent.memory) if m.get("role") == "user" and m.get("content")), None)
        ai_msg = next((m["content"] for m in reversed(agent.memory) if m.get("role") == "assistant" and m.get("content")), None)

        if user_msg and ai_msg:
            engram_data = self._extract_engram(runner, agent, user_msg, ai_msg)

            if engram_data and engram_data.get("importance", 0) >= self.importance_threshold:
                fact = engram_data.get("fact", "")
                if fact:
                    user_id = getattr(agent, "user_id", None)
                    self._save_engram(agent.name, user_id, fact, engram_data["importance"])

        # Cleanup injected context
        self._cleanup_context(agent)

    # --- ASYNC HOOKS ---
    async def before_run_async(self, agent, runner):
        """Async hook: Retrieve engrams before the agent acts."""
        user_id = getattr(agent, "user_id", None)
        rows = await asyncio.to_thread(self._retrieve_engrams, user_id)

        if rows:
            engram_text = self._build_engram_text(rows)
            print(f"[Engram] {len(rows)} core memories injected.")
            agent.memory.insert(len(agent.memory) - 1, {
                "role": "system",
                "content": engram_text
            })

    async def after_run_async(self, agent, runner):
        """Async hook: Extract and save engrams after interaction."""
        user_msg = next((m["content"] for m in reversed(agent.memory) if m.get("role") == "user" and m.get("content")), None)
        ai_msg = next((m["content"] for m in reversed(agent.memory) if m.get("role") == "assistant" and m.get("content")), None)

        if user_msg and ai_msg:
            engram_data = await self._extract_engram_async(runner, agent, user_msg, ai_msg)

            if engram_data and engram_data.get("importance", 0) >= self.importance_threshold:
                fact = engram_data.get("fact", "")
                if fact:
                    user_id = getattr(agent, "user_id", None)
                    await asyncio.to_thread(self._save_engram, agent.name, user_id, fact, engram_data["importance"])

        # Cleanup injected context
        self._cleanup_context(agent)
