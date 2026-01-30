---
title: Agent SDK Middleware System Overview
description: Explore the powerful middleware system of the Agent SDK. Use built-in modules for RAG, safety, logging, or build your own custom extensions.
keywords: 
    - agent middleware
    - python agent sdk
    - ai middleware
    - rag integration
    - safety checks
    - logging system
    - extensibility
---

# Middleware System

Middleware is the backbone of the Agent SDK's extensibility. It allows you to intercept, modify, and monitor the agent's behavior at key points in its lifecycle without changing the core agent code.

By using middleware, you can keep your agent logic clean and focused on reasoning, while offloading cross-cutting concerns like logging, safety, and memory management to separate components.

## How it Works

The Runner executes middleware hooks in a specific order:

1.  **Before Run**: Modifies the agent or context before the reasoning loop starts.
2.  **Before Tool Execution**: intercepts tool calls, allowing for approval or modification.
3.  **After Tool Execution**: Processes the tool output before the agent sees it.
4.  **After Run**: Analyzes or logs the final result of the interaction.

## Available Modules

| Category | Middleware | Description |
| :--- | :--- | :--- |
| **[RAG & Memory](./retrieval-augmented-generation-rag-middleware.md)** | `SimpleRAG` | SQLite-based long-term memory with keyword search. |
| | `ChromaRAG` | Vector-based semantic memory using ChromaDB. |
| **[Memory Mgmt](./memory-management-and-summarization-middleware.md)** | `MemorySummarizer` | Automatically summarizes old conversations to save context. |
| **[Safety](./ai-safety-and-human-control-middleware.md)** | `HumanInTheLoop` | Requires human approval before executing sensitive tools. |
| | `SelfReflection` | "Critic" loop that reviews agent responses for safety/quality. |
| **[Utilities](./agent-logging-and-context-injection-middleware.md)** | `FileLogger` | Logs activity to a JSONL file. |
| | `SQLiteLogger` | Logs activity to a SQLite database. |
| | `ContextInjector` | Injects environment variables and static data into context. |

## Quick Start

```python
from agent_sdk.runner import Runner
from agent_sdk.middleware import FileLogger, HumanInTheLoop

runner = Runner(agent=my_agent, client=my_client)

# Chain multiple middlewares
runner.use(FileLogger("logs.jsonl"))
runner.use(HumanInTheLoop())

runner.run("Delete all files in the current folder.")
# -> Logs start
# -> HumanInTheLoop pauses and asks for permission
```

## Advanced

*   [Building Custom Middleware Extensions](./building-custom-middleware-extensions.md)
