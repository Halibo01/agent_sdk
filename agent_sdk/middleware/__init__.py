"""
Agent SDK Middleware

Middleware components allow you to intercept and modify the agent's behavior at various stages 
of the execution lifecycle (before run, before tool execution, after run).

Documentation: https://docs.agent-sdk-core.dev/modules/middleware

Available Middleware:
- **HumanInTheLoop**: Pauses execution for critical tools to get user approval.
- **FileLogger**: Logs agent activity to a file (JSONL).
- **SQLiteLogger**: Logs activity to a SQLite database.
- **MemorySummarizer**: Compresses conversation history to save tokens.
- **SimpleRAG / ChromaRAG**: Retrieval-Augmented Generation for long-term memory.
- **SelfReflection**: Verification step where an LLM critiques the agent's plan/output.
- **ContextInjector**: Injects static or dynamic variables into the agent's context.
"""

from .logger import FileLogger
from .memory import MemorySummarizer
from .approval import HumanInTheLoop
from .context import ContextInjector
from .storage import SQLiteLogger
from .reflection import SelfReflection
from .rag import SimpleRAG, ChromaRAG


__all__ = [
    "FileLogger",
    "MemorySummarizer",
    "HumanInTheLoop",
    "ContextInjector",
    "SQLiteLogger",
    "SelfReflection",
    "SimpleRAG",
    "ChromaRAG",
]