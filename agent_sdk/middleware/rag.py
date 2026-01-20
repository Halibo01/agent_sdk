from .base import Middleware
import sqlite3
import json
import asyncio
import os

# =============================================================================
# 1. SimpleRAG (SQLite FTS5 Based)
# - Ekstra kütüphane gerektirmez (Built-in).
# - Anahtar kelime (keyword) eşleşmesi yapar.
# - Çok hızlı ve hafiftir.
# =============================================================================

class SimpleRAG(Middleware):
    def __init__(self, db_path: str = "agent_knowledge.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # FTS5 tablosu (Hızlı metin arama için)
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge 
            USING fts5(content, metadata)
        """)
        conn.commit()
        conn.close()

    def _add_memory(self, content: str, metadata: dict):
        if not content or len(content) < 10: return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO knowledge (content, metadata) VALUES (?, ?)", 
                           (content, json.dumps(metadata)))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SimpleRAG] Save Error: {e}")

    def _search_memory(self, query: str, limit: int = 3) -> str:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query'yi güvenli hale getir
            safe_query = query.replace('"', '').replace("'", "")
            if not safe_query.strip(): return ""

            cursor.execute(f"SELECT content FROM knowledge WHERE knowledge MATCH ? ORDER BY rank LIMIT ?", (safe_query, limit))
            results = cursor.fetchall()
            conn.close()
            
            if not results: return ""
            return "\n".join([f"- {r[0]}" for r in results])
        except Exception as e:
            return ""

    # --- HOOKS ---
    def before_run(self, agent, runner):
        if not agent.memory: return
        last_msg = agent.memory[-1]
        if last_msg.get("role") != "user": return
        
        query = last_msg.get("content", "")
        context = self._search_memory(query)
        
        if context:
            print(f"\n[SimpleRAG] Alakalı geçmiş bulundu.")
            agent.memory.insert(len(agent.memory)-1, {
                "role": "system",
                "content": f"RELEVANT MEMORY (Keyword Search):\n{context}"
            })

    def after_run(self, agent, runner):
        if len(agent.memory) < 2: return
        user_msg = next((m["content"] for m in reversed(agent.memory) if m["role"] == "user"), None)
        ai_msg = next((m["content"] for m in reversed(agent.memory) if m["role"] == "assistant"), None)

        if user_msg and ai_msg:
            full_entry = f"User: {user_msg}\nAI: {ai_msg}"
            self._add_memory(full_entry, {"agent": agent.name})

    # --- ASYNC HOOKS ---
    async def before_run_async(self, agent, runner):
        if not agent.memory: return
        last_msg = agent.memory[-1]
        if last_msg.get("role") != "user": return
        
        context = await asyncio.to_thread(self._search_memory, last_msg.get("content", ""))
        if context:
            print(f"\n[SimpleRAG] Alakalı geçmiş bulundu.")
            agent.memory.insert(len(agent.memory)-1, {
                "role": "system",
                "content": f"RELEVANT MEMORY (Keyword Search):\n{context}"
            })

    async def after_run_async(self, agent, runner):
        if len(agent.memory) < 2: return
        user_msg = next((m["content"] for m in reversed(agent.memory) if m["role"] == "user"), None)
        ai_msg = next((m["content"] for m in reversed(agent.memory) if m["role"] == "assistant"), None)
        if user_msg and ai_msg:
            full_entry = f"User: {user_msg}\nAI: {ai_msg}"
            await asyncio.to_thread(self._add_memory, full_entry, {"agent": agent.name})


# =============================================================================
# 2. ChromaRAG (Vector Database Based)
# - 'chromadb' kütüphanesi gerektirir.
# - Anlamsal (Semantic) arama yapar.
# - Daha akıllıdır ama daha ağırdır.
# =============================================================================

class ChromaRAG(Middleware):
    def __init__(self, collection_name: str = "agent_memory", persist_dir: str = "./chroma_db"):
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self.collection = None
        self._init_db()

    def _init_db(self):
        try:
            import chromadb
            # Persistent Client oluştur
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            print(f"[ChromaRAG] ChromaDB initialized at '{self.persist_dir}'. Collection: '{self.collection_name}'")
        except ImportError:
            print("[ChromaRAG] Error: 'chromadb' not found. Please install via 'pip install chromadb' or use SimpleRAG.")
        except Exception as e:
            print(f"[ChromaRAG] Init Error: {e}")

    def _add_memory(self, content: str, metadata: dict):
        if not self.collection: return
        if not content or len(content) < 10: return

        try:
            import uuid
            doc_id = str(uuid.uuid4())
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"[ChromaRAG] Add Error: {e}")

    def _search_memory(self, query: str, limit: int = 2) -> str:
        if not self.collection: return ""
        if not query.strip(): return ""

        try:
            results = self.collection.query(query_texts=[query], n_results=limit)
            docs = results['documents'][0]
            if not docs: return ""
            return "\n".join([f"- {doc}" for doc in docs])
        except Exception as e:
            print(f"[ChromaRAG] Search Error: {e}")
            return ""

    # --- HOOKS ---
    def before_run(self, agent, runner):
        if not agent.memory: return
        last_msg = agent.memory[-1]
        if last_msg.get("role") != "user": return
        
        context = self._search_memory(last_msg.get("content", ""))
        if context:
            print(f"\n[ChromaRAG] Anlamsal hafızadan bilgi getirildi.")
            agent.memory.insert(len(agent.memory)-1, {
                "role": "system",
                "content": f"RELEVANT MEMORY (Semantic Search):\n{context}"
            })

    def after_run(self, agent, runner):
        if len(agent.memory) < 2: return
        user_msg = next((m["content"] for m in reversed(agent.memory) if m["role"] == "user"), None)
        ai_msg = next((m["content"] for m in reversed(agent.memory) if m["role"] == "assistant"), None)
        if user_msg and ai_msg:
            full_entry = f"User: {user_msg}\nAI: {ai_msg}"
            self._add_memory(full_entry, {"agent": agent.name})

    # --- ASYNC HOOKS ---
    async def before_run_async(self, agent, runner):
        if not agent.memory: return
        last_msg = agent.memory[-1]
        if last_msg.get("role") != "user": return
        
        context = await asyncio.to_thread(self._search_memory, last_msg.get("content", ""))
        if context:
            print(f"\n[ChromaRAG] Anlamsal hafızadan bilgi getirildi.")
            agent.memory.insert(len(agent.memory)-1, {
                "role": "system",
                "content": f"RELEVANT MEMORY (Semantic Search):\n{context}"
            })

    async def after_run_async(self, agent, runner):
        if len(agent.memory) < 2: return
        user_msg = next((m["content"] for m in reversed(agent.memory) if m["role"] == "user"), None)
        ai_msg = next((m["content"] for m in reversed(agent.memory) if m["role"] == "assistant"), None)
        if user_msg and ai_msg:
            full_entry = f"User: {user_msg}\nAI: {ai_msg}"
            await asyncio.to_thread(self._add_memory, full_entry, {"agent": agent.name})
