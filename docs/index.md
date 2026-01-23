# Welcome to Agent SDK

**Agent SDK** is a **Streaming-First**, **User-Friendly**, and **modular** AI Agent Framework built for Python.

It is designed to deliver **seamless real-time user experiences** with built-in streaming support, while offering an incredibly intuitive API for developers. Unlike complex alternatives, Agent SDK prioritizes simplicity without sacrificing power.

## 🌟 Key Features

*   **Universal Client Support:** Supports OpenAI, Google Gemini, Anthropic Claude, xAI Grok, DeepSeek, Qwen, Zhipu AI, and local models (Ollama).
*   **Hybrid Architecture:** Supports both Synchronous (`run_stream`) and Asynchronous (`run_stream_async`) execution within the same codebase.
*   **Swarm Intelligence:** Enables agents to recognize each other, delegate tasks, and collaborate (`AgentBridge` and `AgentSwarm`).
*   **Middleware System:** Plug-and-play modules that modify agent behavior:
    *   **RAG (Retrieval-Augmented Generation):** Long-term memory using ChromaDB or SQLite FTS5.
    *   **Human-in-the-Loop:** User approval for critical actions.
    *   **Self-Reflection:** Agents can review and correct their own outputs.
    *   **Logging:** Detailed activity logging.
*   **Advanced Tooling:** 
    *   **Sandbox:** Secure execution of Python code (Docker or Isolated Local Process).
    *   File system, Web search, and Shell command tools.

## Next Steps

*   [Installation](getting-started/installation.md)
*   [Quick Start](getting-started/quickstart.md)