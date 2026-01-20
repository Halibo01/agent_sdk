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
        # user_id sütunu UNINDEXED olarak ekleniyor, böylece full-text search'e dahil olmaz ama saklanır.
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge 
                USING fts5(content, metadata, user_id UNINDEXED)
            """)
        except sqlite3.OperationalError:
            # Fallback for older sqlite versions or if table exists with different schema
            # Note: altering virtual tables is tricky, for now we assume fresh start or compatible schema
            pass
        conn.commit()
        conn.close()

    def _add_memory(self, content: str, metadata: dict, user_id: str = None):
        if not content or len(content) < 10: return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # user_id yoksa 'global' olarak işaretle veya boş bırak
            uid = user_id or "global"
            cursor.execute("INSERT INTO knowledge (content, metadata, user_id) VALUES (?, ?, ?)", 
                           (content, json.dumps(metadata), uid))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SimpleRAG] Save Error: {e}")

    def _search_memory(self, query: str, user_id: str = None, limit: int = 3) -> str:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            safe_query = query.replace('"', '').replace("'", "")
            if not safe_query.strip(): return ""

            # user_id filtresi
            if user_id:
                # FTS5 sorgusunda filtreleme: "sorgu AND user_id: 'uid'" (ama user_id unindexed olduğu için WHERE ile bakmak daha güvenli)
                # Ancak FTS5 sanal tablolarında WHERE user_id = ? bazen tam desteklenmez, FTS syntax kullanmak gerekebilir.
                # En garanti yol: Tüm eşleşmeleri çekip Python tarafında filtrelemek (küçük ölçek için) 
                # veya FTS5 hidden column rowid kullanarak join yapmak.
                # Basitlik için: MATCH sorgusu + WHERE user_id filtresi (SQLite modern versiyonlarında çalışır)
                sql = "SELECT content FROM knowledge WHERE knowledge MATCH ? AND user_id = ? ORDER BY rank LIMIT ?"
                params = (safe_query, user_id, limit)
            else:
                # User ID yoksa sadece global verileri veya hepsini getir? 
                # Güvenlik için: User ID yoksa sadece 'global' olanları getir.
                sql = "SELECT content FROM knowledge WHERE knowledge MATCH ? AND user_id = 'global' ORDER BY rank LIMIT ?"
                params = (safe_query, limit)

            cursor.execute(sql, params)
            results = cursor.fetchall()
            conn.close()
            
            if not results: return ""
            return "\n".join([f"- {r[0]}" for r in results])
        except Exception as e:
            # print(f"[SimpleRAG] Search Error: {e}") 
            return ""

    # --- HOOKS ---
    def before_run(self, agent, runner):
        if not agent.memory: return
        last_msg = agent.memory[-1]
        if last_msg.get("role") != "user": return
        
        query = last_msg.get("content", "")
        # Agent'ın user_id bilgisini kullan
        user_id = getattr(agent, "user_id", None)
        
        context = self._search_memory(query, user_id=user_id)
        
        if context:
            print(f"\n[SimpleRAG] Alakalı geçmiş bulundu (User: {user_id}).")
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
            user_id = getattr(agent, "user_id", None)
            self._add_memory(full_entry, {"agent": agent.name}, user_id=user_id)

    # --- ASYNC HOOKS ---
    async def before_run_async(self, agent, runner):
        if not agent.memory: return
        last_msg = agent.memory[-1]
        if last_msg.get("role") != "user": return
        
        user_id = getattr(agent, "user_id", None)
        context = await asyncio.to_thread(self._search_memory, last_msg.get("content", ""), user_id)
        
        if context:
            print(f"\n[SimpleRAG] Alakalı geçmiş bulundu (User: {user_id}).")
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
            user_id = getattr(agent, "user_id", None)
            await asyncio.to_thread(self._add_memory, full_entry, {"agent": agent.name}, user_id)


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

    def _add_memory(self, content: str, metadata: dict, user_id: str = None):
        if not self.collection: return
        if not content or len(content) < 10: return

        try:
            import uuid
            doc_id = str(uuid.uuid4())
            
            # User ID'yi metadata'ya ekle
            final_metadata = metadata.copy()
            if user_id:
                final_metadata["user_id"] = user_id
            else:
                final_metadata["user_id"] = "global"

            self.collection.add(
                documents=[content],
                metadatas=[final_metadata],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"[ChromaRAG] Add Error: {e}")

    def _search_memory(self, query: str, user_id: str = None, limit: int = 2) -> str:
        if not self.collection: return ""
        if not query.strip(): return ""

        try:
            # User ID filtresi hazırla
            where_filter = None
            if user_id:
                where_filter = {"user_id": user_id}
            else:
                where_filter = {"user_id": "global"} # Veya filtreleme (None) = hepsi

            results = self.collection.query(
                query_texts=[query], 
                n_results=limit,
                where=where_filter # ChromaDB metadata filtresi
            )
            
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
        
        user_id = getattr(agent, "user_id", None)
        context = self._search_memory(last_msg.get("content", ""), user_id=user_id)
        
        if context:
            print(f"\n[ChromaRAG] Anlamsal hafızadan bilgi getirildi (User: {user_id}).")
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
            user_id = getattr(agent, "user_id", None)
            self._add_memory(full_entry, {"agent": agent.name}, user_id=user_id)

    # --- ASYNC HOOKS ---
    async def before_run_async(self, agent, runner):
        if not agent.memory: return
        last_msg = agent.memory[-1]
        if last_msg.get("role") != "user": return
        
        user_id = getattr(agent, "user_id", None)
        context = await asyncio.to_thread(self._search_memory, last_msg.get("content", ""), user_id)
        
        if context:
            print(f"\n[ChromaRAG] Anlamsal hafızadan bilgi getirildi (User: {user_id}).")
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
            user_id = getattr(agent, "user_id", None)
            await asyncio.to_thread(self._add_memory, full_entry, {"agent": agent.name}, user_id)
