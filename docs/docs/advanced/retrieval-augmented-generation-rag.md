---
title: Advanced RAG Integration | Agent SDK
description: Deep dive into Retrieval-Augmented Generation strategies. Compare SimpleRAG vs. ChromaRAG and learn configuration best practices.
keywords: 
    - advanced rag
    - vector search strategies
    - rag configuration
    - knowledge base integration
    - sqlite vs chroma
    - semantic search
---

# RAG Integration

Retrieval-Augmented Generation (RAG) allows agents to remember past conversations or access external knowledge bases.

## SimpleRAG (SQLite)

The `SimpleRAG` middleware provides a lightweight, zero-dependency (other than standard libraries) solution using SQLite's FTS5 (Full-Text Search).

### Features
*   **Keyword Search:** Fast retrieval of past messages matching user queries.
*   **Context Injection:** Automatically injects relevant history into the system prompt.
*   **Session Management:** Groups messages by session IDs and generates titles.

### Configuration

```python
from agent_sdk.middleware import SimpleRAG

# Initialize
rag = SimpleRAG(
    db_path="my_memory.db",
    title_summary=True,        # Use LLM to generate titles for sessions
    summary_model="gpt-4o"     # Optional: Use a cheaper model for titles (must be the same model type from client)
)

runner.use(rag)
```

## ChromaRAG (Vector Database)

For more advanced, semantic understanding (e.g., knowing that "canine" relates to "dog"), use `ChromaRAG`.

### Prerequisites
```bash
pip install chromadb
```

### Configuration

```python
from agent_sdk.middleware import ChromaRAG

# Initialize
chroma_rag = ChromaRAG(
    persist_dir="./chroma_data",
    collection_name="agent_memory"
)

runner.use(chroma_rag)
```

### How it Works
1.  **Before Run:** The middleware takes the user's latest message, generates an embedding, and queries the database.
2.  **Context:** The most relevant documents are inserted into the agent's memory with a "system" role.
3.  **After Run:** The new conversation turn (User + AI response) is saved to the database.