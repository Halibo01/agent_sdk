# Agent SDK 🤖

**Agent SDK** is a **Streaming-First**, **User-Friendly**, and **modular** AI Agent Framework built for Python.

It is designed to deliver **seamless real-time user experiences** with built-in streaming support, while offering an incredibly intuitive API for developers. Unlike complex alternatives, Agent SDK prioritizes simplicity without sacrificing power.

Inspired by libraries like LangChain and AutoGen, it provides a lightweight, controllable, and production-ready environment.

## 🌟 Features

*   **Universal Client Support:** Supports OpenAI, Google Gemini, Anthropic Claude, xAI Grok, DeepSeek, Qwen, Zhipu AI, and local models (Ollama).
*   **Hybrid Architecture:** Supports both Synchronous (`run_stream`) and Asynchronous (`run_stream_async`) execution within the same codebase.
*   **Swarm Intelligence:** Enables agents to recognize each other, delegate tasks, and collaborate (`AgentBridge`).
*   **Middleware System:** Plug-and-play modules that modify agent behavior:
    *   🧠 **RAG (Retrieval-Augmented Generation):** Long-term memory using ChromaDB or SQLite FTS5.
    *   🛡️ **Human-in-the-Loop:** User approval for critical actions.
    *   🤔 **Self-Reflection:** Agents can review and correct their own outputs.
    *   📝 **Logging:** Detailed activity logging via JSONL or SQLite.
    *   📚 **Summarization:** Automatically compresses conversation history to maintain context limits.
    *   💉 **Context Injection:** Inject runtime environment variables or static data into agent memory.
*   **Advanced Tooling:** 
    *   **Sandbox:** Secure execution of Python code (Docker or Isolated Local Process).
    *   File system, Web search, and Shell command tools.

## 📦 Installation

Install easily via pip:

```bash
pip install agent-sdk-core
```

### 👨‍💻 For Development

If you want to contribute or modify the source code:

```bash
git clone https://github.com/Halibo01/agent_sdk.git
cd agent_sdk
pip install -e .[all]
```

To install only specific dependencies:

```bash
pip install -e .[openai]   # Only OpenAI support
pip install -e .[gemini]   # Only Gemini support
pip install -e .[rag]      # Only RAG (ChromaDB) support
```

## 🔑 Configuration

Security Best Practice: Use environment variables for API keys.

1. Create a `.env` file in your project root:
   ```ini
   OPENAI_API_KEY=sk-...
   GEMINI_API_KEY=AIza...
   ANTHROPIC_API_KEY=sk-ant...
   ```

2. Load them in your python script:
   ```python
   import os
   from dotenv import load_dotenv
   from agent_sdk import OpenAIClient

   load_dotenv() # Loads variables from .env
   
   client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
   ```

## ⚡ Simple Usage (Direct LLM Access)

You don't always need Agents or Runners. You can use the unified Client interface for direct LLM calls.

```python
from agent_sdk import OpenAIClient

# 1. Initialize any client
client = OpenAIClient(api_key="sk-...")
# or client = GeminiClient(api_key="AIza...")

messages = [{"role": "user", "content": "What is the capital of France?"}]

# 2. Simple Chat (Sync)
response = client.chat(model="gpt-4o", messages=messages)
print(response["content"])

# 3. Streaming Chat (Sync)
stream = client.chat_stream(model="gpt-4o", messages=messages)
for event in stream:
    print(event, end="", flush=True)

# 4. Async Support
# await client.chat_async(...)
# async for event in client.chat_stream_async(...): ...
```

## 🔌 Client Usage

You can use any LLM provider easily:

```python
from agent_sdk import Runner, OpenAIClient, GeminiClient, AnthropicClient, OllamaClient, DeepSeekClient

# 1. OpenAI (or compatible APIs like Grok, Qwen)
client = OpenAIClient(api_key="sk-...")

# 2. Google Gemini
client = GeminiClient(api_key="AIza...")

# 3. Anthropic Claude
client = AnthropicClient(api_key="sk-ant...")

# 4. Local Models (Ollama)
client = OllamaClient(base_url="http://localhost:11434")

# 5. DeepSeek
client = DeepSeekClient(api_key="sk-...")

# Initialize Runner with any client
runner = Runner(client)
```
Q: Why do we have different clients for every AI API?
A: While standard chat responses are often similar, streaming formats and tool calling specifications vary significantly between providers. Using the specific client ensures correct parsing of streams and reliable tool execution.

## 🚀 Quick Start (Agent Mode)

Let's create a simple assistant:

```python
from agent_sdk import Runner, Agent, OpenRouterClient

client = OpenRouterClient(api_key="sk-...")
runner = Runner(client)

assistant = Agent(
    name="Assistant",
    model="mistralai/mistral-7b-instruct",
    instructions="You are a helpful assistant."
)

stream = runner.run_stream(assistant, "Hello, how are you?")

for event in stream:
    if event.type == "token":
        print(event.data, end="", flush=True)
```

### 🔄 How the Runner Works (The Loop)

The `Runner` orchestrates the **ReAct (Reasoning + Acting)** loop, making the agent autonomous:

1.  **Think:** Runner sends history + instructions to the LLM.
2.  **Decide:** LLM decides to call a tool (e.g., `web_search`) or respond to the user.
3.  **Act:** If a tool is chosen, Runner executes the Python function securely.
4.  **Observe:** The tool's output (or error) is fed back to the LLM.
5.  **Repeat:** The process repeats until the Agent is satisfied.

*Self-Correction: If a tool raises an error (e.g., `FileNotFoundError`), the error message is sent back to the Agent. The Agent then tries to fix the mistake (e.g., by creating the file) in the next turn.*

## 🛠️ Creating Custom Tools

You can turn any Python function into a tool using decorators. The `@tool_message` decorator allows you to define a custom status message that is displayed when the agent invokes the tool.

For sensitive operations, use `@approval_required` to pause execution and request user confirmation. This works in tandem with the `HumanInTheLoop` middleware. You can customize the approval logic (e.g., integrate with Slack/Discord or a web UI) by passing a custom callback to the middleware.

```python
from agent_sdk import tool_message, approval_required

# 1. Basic Tool
@tool_message("Calculating {a} + {b}...")
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b

# 2. Critical Tool (Requires Approval Middleware (HumanInTheLoop))
@approval_required
@tool_message("Deleting file: {path}")
def delete_file(path: str) -> str:
    """Deletes a file from the system."""
    # dangerous code here...
    return f"File {path} deleted."

# 3. Async Tool (Automatically supported)
@tool_message("Fetching data from {url}...")
async def fetch_data(url: str) -> str:
    """Fetches data asynchronously."""
    # async implementation...
    return "Data"

# Usage in Agent
agent = Agent(
    name="Worker",
    instructions="Use tools when needed.",
    tools={"add": add, "delete": delete_file, "fetch": fetch_data}
)

```

> **💡 Best Practice:** Always catch exceptions inside your tools and return the error message as a string. This allows the Agent to see the error and attempt to fix it (Self-Correction), rather than crashing the loop.
>
> ```python
> def safe_tool(arg):
>     try:
>         # ... logic ...
>     except Exception as e:
>         return f"Error: {str(e)}" # Agent reads this and uses an alternative plan.
> ```


## 🛡️ Human-in-the-Loop & Approval Mechanism

Agent SDK includes a robust **Human-in-the-Loop (HITL)** system to prevent agents from performing unauthorized or dangerous actions (e.g., deleting files, executing shell commands, or making financial transactions).

### 1. Marking Tools for Approval

To require approval for a specific tool, use the `@approval_required` decorator.

```python
from agent_sdk import approval_required, tool_message

@approval_required
@tool_message("Executing critical command: {command}")
def execute_sensitive_command(command: str):
    """Executes a system command."""
    # ... implementation ...
    return "Done"
```

### 2. Enabling the Middleware

The `HumanInTheLoop` middleware intercepts any tool marked with `@approval_required`. If no callback is provided, it defaults to a **CLI-based interactive prompt** (`input("[Y/n]")`).

```python
from agent_sdk import Runner
from agent_sdk.middleware import HumanInTheLoop

runner = Runner(client)
runner.use(HumanInTheLoop()) # Default CLI mode
```

### 3. Custom Callbacks (Web & API Integration)

For Web UIs or APIs, you can provide a custom `approval_callback`. This function receives the agent name, tool name, arguments, and a unique `call_id`.

```python
def my_web_callback(agent_name, tool_name, args, call_id):
    # 1. Log the request or send a notification (Slack, WebSocket, etc.)
    print(f"Pending approval for {tool_name} with ID {call_id}")
    
    # 2. Return "approve" to proceed, "reject" to block
    # In a real API, you might check a database or a list of approved IDs.
    if call_id in my_approved_list:
        return "approve"
    
    return "reject"

runner.use(HumanInTheLoop(approval_callback=my_web_callback))
```

### 4. Stateful vs. Stateless Verification

When building APIs (like `api_server.py`), the connection is often stateless. To handle retries or page refreshes, the HITL system supports two types of IDs:

*   **`call_id`**: A unique ID generated for each specific tool call attempt. Best for single-session stateful tracking.
*   **`signature`**: A deterministic hash of the `tool_name` and its `arguments`. If the agent tries to call the exact same tool with the exact same parameters again, the signature will be identical. This allows for "Stateless Approval" where the client can remember that a specific action was already authorized.

### 5. API Flow Example

1.  **Request:** Client sends a task to `/chat/stream`.
2.  **Intercept:** Agent tries to use a protected tool. Middleware triggers.
3.  **Event:** Server emits a `type: "approval_required"` event and pauses execution. The event data contains the `tool_call_id` (signature).
4.  **User Action:** User clicks "Approve" on the UI.
5.  **Retry:** Client re-sends the same request, but includes the signature in the `approved_tool_ids` list.
6.  **Success:** Middleware checks the list, finds the signature, and allows the tool to run.

## 🛡️ Code Sandbox & State Management

Agent SDK provides a `LocalSandbox` for executing Python code generated by agents. This allows agents to perform calculations, data analysis, or logic tasks securely.

**Key Concepts:**
*   **State Persistence (`locals`):** Variables defined in one execution block persist to the next. The sandbox maintains a local scope across executions.
*   **Custom Context (`globals`):** You can inject your own functions, variables, or libraries into the sandbox environment, making them available for the agent to use directly in the code it writes.
```python
from agent_sdk.sandbox import LocalSandbox
import pandas as pd

# 1. Define custom tools/variables
def my_custom_tool(x):
    return x * 2

# 2. Initialize Sandbox with context
# Pass libraries or functions to be available in the code environment
sandbox = LocalSandbox(custom_globals={
    "double_it": my_custom_tool,
    "pd": pd  
})

# 3. Execution preserves state (Locals)
sandbox.run_code("x = 10")
sandbox.run_code("y = double_it(x)") # Uses injected global 'double_it'
result = sandbox.run_code("print(y)") # Output: 20
```

## 📡 Stream Events Output

The SDK provides real-time feedback through event objects. The type of event depends on whether you are using the high-level `Runner` (Agent Mode) or the low-level `Client` (Direct Mode).

### 1. Agent Mode (`AgentStreamEvent`)

Returned by `runner.run_stream()`. Includes context about which agent produced the event and covers the full lifecycle of tool execution.

| Attribute    | Type   | Description |
| :---         | :---   | :--- |
| `type`       | `str`  | Event type (e.g., `"token"`, `"tool_call_ready"`). |
| `data`       | `Any`  | Content payload. |
| `agent_name` | `str`  | Name of the agent. |

### 2. Client Mode (`StreamEvent`)

Returned by `client.chat_stream()`. A lightweight wrapper for raw LLM outputs.

| Attribute | Type  | Description |
| :---      | :---  | :--- |
| `type`    | `str` | Event type. |
| `data`    | `Any` | Content payload. |

### Common Event Types

*   **`"token"`**: A chunk of text from the LLM response. (`data`: `str`)
*   **`"reasoning"`**: Thinking process content (for models like DeepSeek R1). (`data`: `str`)
*   **`"error"`**: Critical errors. (`data`: `str`)

### Agent-Specific Events (Runner Only)

*   **`"tool_call_ready"`**: Emitted before a tool is executed. Contains resolved function name and arguments. (`data`: `List[dict]`)
*   **`"tool_result"`**: Emitted after a tool finishes execution. Contains the output. (`data`: `dict`)

### Handling Code Example (Agent Mode)

```python
for event in stream:
    # 1. Standard Response Text
    if event.type == "token":
        print(event.data, end="", flush=True)
    
    # 2. Reasoning / Thinking Process
    elif event.type == "reasoning":
        print(f"\033[90m{event.data}\033[0m", end="", flush=True) # Print in gray

    # 3. Tool Execution Lifecycle
    elif event.type == "tool_call_ready":
        tool_info = event.data[0]['function']
        print(f"\n[Agent: {event.agent_name}] 🛠️ Calling: {tool_info['name']}({tool_info['arguments']})")

    elif event.type == "tool_result":
        print(f"\n✅ Result: {event.data['output']}")
    
    # 4. Errors
    elif event.type == "error":
        print(f"\n❌ Error: {event.data}")
```

## 🧠 Advanced Usage

### 1. Multi-Agent Swarm Setup

Create a collaborative environment where agents form a fully connected **mesh network**. Each agent receives tools to communicate with every other agent in the swarm.

Example: Collaboration between a Manager and a Coder agent:

```python
from agent_sdk import Agent, AgentSwarm
from agent_sdk.tools import run_python_code

manager = Agent(name="Manager", instructions="Analyze the task and delegate to Coder.")
coder = Agent(
    name="Coder", 
    instructions="Write Python code.", 
    tools={"run_code": run_python_code}
)

swarm = AgentSwarm(runner)
swarm.add_agent(manager)
swarm.add_agent(coder)
swarm.connect_all() # Builds a mesh network (Manager <-> Coder)

runner.run_stream(manager, "Write a code that finds prime numbers from 1 to 100.")
```

#### 🌉 AgentBridge: Under the Hood

The `AgentSwarm` uses `AgentBridge` internally to connect agents. However, you can use `AgentBridge` directly to create manual connections or hierarchical structures.

`AgentBridge` wraps a target agent as a callable tool for another agent, handling message passing and event forwarding automatically.

```python
from agent_sdk import AgentBridge

# 1. Create Agents
manager = Agent(name="Manager", instructions="Manage the team.")
coder = Agent(name="Coder", instructions="Write Python code.")

# 2. Bridge the Coder to the Manager
# This creates a tool named 'ask_coder(task: str)' and adds it to Manager's tools.
bridge = AgentBridge(agent=coder, runner=runner)
manager.tools["ask_coder"] = bridge.create_tool()

# 3. Manager can now call the Coder
runner.run_stream(manager, "Write a snake game.") 
# Flow: Manager -> calls ask_coder("Write a snake game") -> Coder executes -> Result returns to Manager -> Manager returns to you
```

**Comparison:**
*   **`AgentBridge`**: Creates a **one-way** connection (Agent A can call Agent B). Use this for hierarchical structures (e.g., Manager delegates to Worker).
*   **`AgentSwarm`**: Automatically creates a **mesh network** where every agent can call every other agent. Use this for collaborative teams where roles are fluid.

### 2. Middleware Ecosystem

Middleware modules allow you to intercept and modify agent behavior at various stages (before run, before tool execution, after run).

```python
from agent_sdk.middleware import (
    HumanInTheLoop, 
    FileLogger, 
    MemorySummarizer, 
    SimpleRAG, 
    ChromaRAG, 
    SelfReflection, 
    ContextInjector
)

# 1. Human Approval for Critical Tools
# Intercepts tools marked with @approval_required
runner.use(HumanInTheLoop())

# 2. Activity Logging
# Logs all tool usages and responses to a JSONL file
runner.use(FileLogger(filename="agent_logs.jsonl"))

# 3. Memory Management (Summarization)
# Compresses memory when it exceeds 15 messages, keeping the last 5
runner.use(MemorySummarizer(threshold=15, keep_last=5))

# 4. Long-Term Memory (RAG)
# SimpleRAG: Lightweight, keyword-based (SQLite FTS5)
runner.use(SimpleRAG(db_path="knowledge.db"))
# ChromaRAG: Semantic, vector-based (Requires `pip install chromadb`)
# runner.use(ChromaRAG(persist_dir="./chroma_db"))

# 5. Self-Correction
# An internal critic reviews the agent's output for errors or safety issues
runner.use(SelfReflection())

# 6. Context Injection
# Automatically adds environment info to the agent's context
runner.use(ContextInjector(env_keys=["USER", "OS"], static_context={"Environment": "Production"}))
```

### 3. Creating Custom Middleware

You can inspect or modify the agent loop by inheriting from the `Middleware` class.

```python
from agent_sdk.middleware.base import Middleware
import time

class PerformanceMonitor(Middleware):
    def __init__(self):
        self.start_time = 0

    def before_run(self, agent, runner): # Runner builtin function
        self.start_time = time.time()
        print(f"🚀 [Monitor] Starting agent: {agent.name}")

    def before_tool_execution(self, agent, runner, tool_name, tool_args): # Runner builtin function
        print(f"🔧 [Monitor] Tool call detected: {tool_name}")
        # Return False to cancel the tool execution if needed!
        return True 

    def after_run(self, agent, runner): # Runner builtin function
        elapsed = time.time() - self.start_time
        print(f"🏁 [Monitor] Finished in {elapsed:.2f} seconds.")

# Usage
runner.use(PerformanceMonitor())
```

### 3. Asynchronous Execution (Async)

For high-performance applications (FastAPI, etc.):

```python
import asyncio

async def main():
    stream = runner.run_stream_async(agent, "Reply fast!")
    async for event in stream:
        print(event)

asyncio.run(main())
```

## 🛠️ Testing

To run all tests:

```bash
python -m unittest discover tests
# or
pytest tests/
```

## 🔗 API Keys & Providers

To use the SDK, you'll need API keys from your preferred AI providers.

| Provider | Supported Models | Get API Key |
| :--- | :--- | :--- |
| **OpenAI** | GPT-4o, GPT-3.5 Turbo | [OpenAI Platform](https://platform.openai.com/api-keys) |
| **Google** | Gemini 1.5 Pro, Flash | [Google AI Studio](https://aistudio.google.com/) |
| **Anthropic** | Claude 3.5 Sonnet, Opus | [Anthropic Console](https://console.anthropic.com/) |
| **OpenRouter** | *Unified Access (All Models)* | [OpenRouter Keys](https://openrouter.ai/keys) (My Personal Favorite) |
| **xAI (Grok)** | Grok-2, Grok Beta | [xAI Console](https://console.x.ai/) |
| **DeepSeek** | DeepSeek V3, R1 | [DeepSeek Platform](https://platform.deepseek.com/) |
| **Ollama** | Llama 3, Mistral (Local) | [Download Ollama](https://ollama.com/) (No Key) |
| **Groq Cloud** | *Fast Inference (Llama/Mixtral)* | [Groq Console](https://console.groq.com/keys) |

## 📄 License

MIT License.