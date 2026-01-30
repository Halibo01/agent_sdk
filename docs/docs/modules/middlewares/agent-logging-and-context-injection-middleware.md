---
title: Agent Logging & Context Injection | Agent SDK
description: Debug and audit your AI agents using FileLogger and SQLiteLogger. Inject environment context dynamically with ContextInjector.
keywords: 
    - agent logging
    - debugging ai
    - context injection
    - file logger
    - sqlite logger
    - environment variables
    - audit trails
---

# Logging & Context Utilities

These middlewares help in debugging, auditing, and providing static knowledge to your agents.

---

## FileLogger

`FileLogger` is a simple, file-based logging system that records every agent interaction, tool usage, and error. It is essential for debugging and reviewing agent performance.

### Usage

```python
from agent_sdk.middleware import FileLogger

# Logs to a JSONL file (JSON Lines)
runner.use(FileLogger(filename="agent_activity.jsonl"))
```

### Log Format
Each line in the file is a JSON object containing:
*   `timestamp`: ISO 8601 time.
*   `type`: Event type (e.g., `tool_attempt`, `run_complete`).
*   `agent`: Name of the agent.
*   `details`: Arguments, results, or message content.

---

## SQLiteLogger

`SQLiteLogger` provides structured logging into a SQLite database. This is better for querying logs programmatically (e.g., "Find all times the agent used the 'search' tool").

### Usage

```python
from agent_sdk.middleware import SQLiteLogger

runner.use(SQLiteLogger(db_path="logs.db"))
```

### Schema
It creates a table `activity_logs` with columns:
*   `id`
*   `timestamp`
*   `agent_name`
*   `event_type`
*   `summary`
*   `details` (JSON)

---

## ContextInjector

`ContextInjector` allows you to inject static information or environment variables into the agent's memory at the start of a session. This is useful for giving the agent awareness of its running environment (e.g., "You are running on Windows", "The user is an Admin").

### Usage

```python
from agent_sdk.middleware import ContextInjector

context = ContextInjector(
    env_keys=["OS", "USERNAME", "PROJECT_ROOT"], # Read these from OS environment
    static_context={
        "Role": "DevOps Engineer",
        "PermissionLevel": "High"
    }
)

runner.use(context)
```

### Effect
It appends a System message to the agent's memory:

```text
[SYSTEM NOTICE: The following context is active for this session]
--- Environment Context ---
OS: Windows_NT
USERNAME: admin
--- Runtime Context ---
Role: DevOps Engineer
PermissionLevel: High
```
