import sqlite3
import json
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
    
    def __init__(self, db_path: str = "agent_engrams.db", importance_threshold: int = 5):
        self.db_path = db_path
        self.importance_threshold = importance_threshold
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Create Engrams table
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
        # Create FTS5 virtual table for fast semantic/keyword searching of engrams
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS engrams_search USING fts5(
                memory_trace, content='engrams', content_rowid='id'
            )
        ''')
        conn.commit()
        conn.close()

    def _extract_engram(self, runner, user_text: str, agent_text: str) -> Optional[Dict]:
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
            # We use a fast/cheap model if available, fallback to agent's default model
            messages = [{"role": "user", "content": prompt}]
            # Disable streaming for this internal cognitive process
            response = runner.client.chat(model="gpt-4o-mini", messages=messages, temperature=0.0) 
            content = response["content"].strip()
            
            # Clean markdown code blocks if present
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            
            data = json.loads(content.strip())
            return data
        except Exception as e:
            # Silently fail cognitive extraction if JSON parsing fails
            return None

    def after_run(self, agent, runner):
        """After interaction, form a new Engram."""
        if len(agent.memory) < 2: return
        
        # Get the last exchange
        user_msg = agent.memory[-2].get("content", "")
        agent_msg = agent.memory[-1].get("content", "")
        
        if not user_msg or not agent_msg: return

        # Cognitive Extraction
        engram_data = self._extract_engram(runner, user_msg, agent_msg)
        
        if engram_data and engram_data.get("importance", 0) >= self.importance_threshold:
            fact = engram_data.get("fact", "")
            if fact:
                self._save_engram(agent.name, agent.user_id, fact, engram_data["importance"])

    def _save_engram(self, agent_name: str, user_id: str, fact: str, importance: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO engrams (timestamp, agent_name, user_id, memory_trace, importance) VALUES (?, ?, ?, ?, ?)",
            (now, agent_name, user_id or "global", fact, importance)
        )
        row_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO engrams_search (rowid, memory_trace) VALUES (?, ?)",
            (row_id, fact)
        )
        conn.commit()
        conn.close()
        print(f"[Engram] Memory formed (Importance {importance}/10): {fact}")

    def before_run(self, agent, runner):
        """Retrieve recent or highly important Engrams before the agent acts."""
        # For a true cognitive architecture, we fetch the top 5 most important/recent engrams for this user.
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Fetch the 5 most important memories for this specific user
        cursor.execute('''
            SELECT timestamp, importance, memory_trace 
            FROM engrams 
            WHERE user_id = ? OR user_id = 'global'
            ORDER BY importance DESC, timestamp DESC 
            LIMIT 5
        ''', (agent.user_id or "global",))
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            engram_text = "CORE MEMORIES (Engrams):\n"
            for row in rows:
                time_str = datetime.datetime.fromisoformat(row[0]).strftime("%Y-%m-%d %H:%M")
                engram_text += f"[{time_str}] (Importance: {row[1]}/10) {row[2]}\n"
            
            agent.memory.insert(0, {"role": "system", "content": engram_text})
