# Middleware System

Middleware allows you to intercept and modify the agent's behavior at various lifecycle stages (Before Run, After Run, Before Tool Execution).

## Built-in Middlewares

### 1. Human In The Loop (`HumanInTheLoop`)
Prevents agents from executing dangerous tools without user permission.

```python
from agent_sdk.middleware import HumanInTheLoop

# Default: Asks for confirmation in CLI using input()
runner.use(HumanInTheLoop())

# Custom: Callback for Web/API integration
def approval_callback(agent_name, tool_name, args, call_id):
    # Logic to check database or wait for user signal
    return "approve" 

runner.use(HumanInTheLoop(approval_callback=approval_callback))
```

### 2. File Logger (`FileLogger`)
Logs all interactions to a JSONL file for debugging or analysis.

```python
from agent_sdk.middleware import FileLogger

runner.use(FileLogger(filename="logs/agent_activity.jsonl"))
```

### 3. RAG (Retrieval-Augmented Generation)
Adds long-term memory capabilities.

*   **SimpleRAG:** SQLite-based, keyword search (FTS5). Good for simple history.
*   **ChromaRAG:** Vector-based, semantic search. Requires `chromadb`.

```python
from agent_sdk.middleware import SimpleRAG

# Automatically summarizes sessions and recalls relevant past conversations
runner.use(SimpleRAG(db_path="memory.db", title_summary=True))
```

### 4. Self Reflection (`SelfReflection`)
Adds a step where the agent (or a separate "Critic" model) reviews the output before showing it to the user. *Implementation may vary.*

## Creating Custom Middleware

You can inherit from the `Middleware` base class to create your own plugins.

```python
from agent_sdk.middleware.base import Middleware

class MyCustomMiddleware(Middleware):
    def before_run(self, agent, runner):
        print(f"Agent {agent.name} is starting a new task!")

    def before_tool_execution(self, agent, runner, tool_name, tool_args, tool_call_id):
        if tool_name == "delete_database":
            print("Blocking dangerous tool!")
            return False # Cancels execution
        return True

runner.use(MyCustomMiddleware())
```