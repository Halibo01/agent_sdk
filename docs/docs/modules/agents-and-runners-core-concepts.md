---
title: Agents & Runners | Agent SDK
description: Understand the core concepts of Agents and Runners. Learn how to define agent instructions, manage state, and execute reasoning loops.
keywords: 
    - ai agent
    - runner
    - reasoning loop
    - agent definition
    - python agent
    - streaming response
    - agent state
---

# Agents & Runners

The core of the SDK revolves around the `Agent` configuration and the `Runner` execution engine.

## The Agent

An `Agent` is a declarative object that defines **who** the AI is and **what** it can do. It doesn't execute anything itself; it holds the state and configuration.

```python
from agent_sdk import Agent

agent = Agent(
    name="Researcher",
    model="gpt-4o",
    instructions="You are an expert researcher. Use tools to find information.",
    tools={...},           # Dictionary of tool functions
    max_steps=10,          # Max tool loops per request to prevent infinite loops
    generation_config={
        "temperature": 0.5,
        "max_tokens": 1000
    }
)
```

### Attributes

*   `name` (str): The display name of the agent.
*   `model` (str): The model identifier string (e.g., "gpt-4o", "gemini-1.5-pro").
*   `instructions` (str): The system prompt that defines behavior and personality.
*   `tools` (dict): A dictionary mapping tool names to python functions.
*   `memory` (list): The conversation history (automatically managed by the Runner).

## The Runner

The `Runner` orchestrates the "Think-Act-Observe" loop (ReAct pattern). It handles:

1.  Formatting messages for the LLM.
2.  Streaming the LLM's response.
3.  Detecting and executing tool calls.
4.  Feeding tool outputs back to the LLM.
5.  Managing Middleware hooks.

### Initialization

```python
from agent_sdk import Runner, OpenAIClient

client = OpenAIClient(api_key="...")
runner = Runner(client)
```

### Execution Methods

#### `run_stream(agent, task)`
Runs the agent synchronously. Returns a generator of `AgentStreamEvent`.

```python
stream = runner.run_stream(agent, "Check the weather in London")
for event in stream:
    if event.type == "token":
        print(event.data, end="")
    elif event.type == "tool_call_ready":
        print(f"\n[Using Tool]: {event.data}")
```

#### `run_stream_async(agent, task)`
Runs the agent asynchronously. Ideal for web servers (FastAPI, etc.).

```python
stream = runner.run_stream_async(agent, "Check the weather in London")
async for event in stream:
    # ... handle events
```

### Events (`AgentStreamEvent`)

The runner emits events to let you build rich UIs.

| Event Type |
| :--- | 
| `token` | A text chunk from the LLM. | `str` |
| `reasoning` | A "thought" chunk (for reasoning models like DeepSeek R1). | `str` |
| `tool_call_ready` | The agent wants to call a tool. | `dict` (function name, args) |
| `tool_result` | The output of a tool execution. | `dict` (output, error) |
| `error` | An error occurred. | `str` |
| `final` | The final response text (emitted at the end). | `dict` or `str` |

```