---
title: RAG & Knowledge Middlewares for Agent SDK
description: Learn how to implement Retrieval-Augmented Generation (RAG) in your agents using SimpleRAG (SQLite) and ChromaRAG (Vector DB) for long-term memory.
keywords: 
    - rag
    - retrieval augmented generation
    - agent memory
    - vector database
    - chromadb
    - sqlite fts5
    - knowledge base
---

# RAG & Knowledge Middlewares

Retrieval-Augmented Generation (RAG) middlewares provide your agents with long-term memory and access to external knowledge bases. This allows agents to recall past conversations, access documentation, or query large datasets that don't fit into the context window.

The SDK provides two built-in RAG implementations:

1.  **SimpleRAG**: A lightweight, file-based solution using SQLite FTS5 (Keyword Search).
2.  **ChromaRAG**: A robust, vector-based solution using ChromaDB (Semantic Search).

---

## Loading External Context

Often, you want to pre-load your agent with specific documents (policies, FAQs, code files) before it starts running. Since the internal method `_add_memory` handles storage, you can use it to inject data manually.

### Ingesting Files Manually

You can write a simple script to read files and pass them to the middleware's storage method.

```python
from agent_sdk.middleware import SimpleRAG
import os

rag = SimpleRAG()

def ingest_file(rag_instance, file_path, metadata=None):
    if metadata is None: metadata = {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Access the internal method to save data
    # content: The text to save
    # metadata: Dict for filtering (e.g., source, type)
    # user_id: Owner of the data (optional)
    rag_instance._add_memory(content, metadata, user_id="global")
    print(f"Ingested: {file_path}")

# Example Usage
ingest_file(rag, "docs/company_policy.txt", metadata={"type": "policy"})
ingest_file(rag, "docs/faq.md", metadata={"type": "faq"})

# Now use this pre-loaded RAG in your runner
# runner.use(rag)
```

**Note:** For `ChromaRAG`, the process is identical as it also implements `_add_memory`.

---

## SimpleRAG

`SimpleRAG` is perfect for local development, maintaining chat history, and simple keyword-based retrieval. It requires no external vector database servers.

### Features
*   **Keyword Search**: Uses SQLite's FTS5 engine for fast text matching.
*   **Session Management**: Automatically tracks user sessions and chat history.
*   **Auto-Titling**: Can generate concise titles for chat sessions using an LLM.
*   **Zero Dependencies**: Uses Python's built-in `sqlite3` library.

### Usage

```python
from agent_sdk.middleware import SimpleRAG

# Initialize the middleware
rag = SimpleRAG(
    db_path="agent_knowledge.db",  # Where to save the database
    title_summary=True,            # Enable AI-generated titles
    summary_model="gemini-2.0-flash" # Model to use for generating titles
)

# Add to your runner
runner.use(rag)
```

### How it works
1.  **Before Run**: It scans the agent's memory (specifically the last user message) and searches the database for relevant keywords.
2.  **Injection**: Relevant past messages are injected into the agent's system prompt under a "RELEVANT MEMORY" section.
3.  **After Run**: The current conversation turn (User + AI response) is saved to the database. If it's a new session, a title is generated.

---

## ChromaRAG

`ChromaRAG` provides **semantic search** capabilities. Unlike keyword search, it understands the *meaning* of the text. For example, searching for "fruit" might retrieve "apple" even if the word "fruit" isn't explicitly mentioned. 

### Multimodal RAG & Custom Embeddings (v0.2.0)
Starting from v0.2.0, `ChromaRAG` supports **Multimodal Embeddings**. This means you can save images, videos, or audio into the database, and search for them using text!

To do this, you inject a custom `embedding_function` into the middleware.

```python
from agent_sdk.middleware import ChromaRAG
from agent_sdk.embeddings.imagebind_embedder import ImageBindEmbeddingFunction
# Or use Gemini's multimodal API: from agent_sdk.embeddings.gemini import GeminiMultimodalEmbedding

# 1. Initialize the embedding model (runs locally)
multimodal_embedder = ImageBindEmbeddingFunction(device="cuda")

# 2. Inject it into ChromaRAG
vector_rag = ChromaRAG(
    collection_name="agent_memory",
    persist_dir="./chroma_db",
    embedding_function=multimodal_embedder
)

# 3. Add to your runner
runner.use(vector_rag)

# Now you can add videos or images to memory!
vector_rag._add_memory(content="vacation_video.mp4", metadata={"type": "video", "year": "2023"})
```

### Prerequisites
You need to install the `chromadb` package:
```bash
pip install chromadb
```

### Usage

```python
from agent_sdk.middleware import ChromaRAG

# Initialize the middleware
vector_rag = ChromaRAG(
    collection_name="agent_memory",
    persist_dir="./chroma_db"      # Where to store vector data
)

# Add to your runner
runner.use(vector_rag)
```

### Comparison: SimpleRAG vs ChromaRAG

| Feature | SimpleRAG | ChromaRAG |
| :--- | :--- | :--- |
| **Search Type** | Keyword (Exact match) | Semantic (Meaning-based) |
| **Storage** | SQLite (.db file) | ChromaDB (Vector store) |
| **Speed** | Very Fast | Fast (depends on embedding size) |
| **Setup** | Built-in | Requires `pip install chromadb` |
| **Best For** | Chat logs, exact quotes, low resource | Knowledge bases, fuzzy retrieval |

---

## Best Practices

*   **Don't use both at once** unless you have a specific reason (e.g., hybrid search). It usually adds too much context.
*   **Context Window**: Both middlewares inject data into the system prompt. Be mindful of your LLM's context limit.
*   **Session IDs**: Ensure your `Agent` instances have `session_id` and `user_id` attributes set if you want to segregate memory by user or conversation.
