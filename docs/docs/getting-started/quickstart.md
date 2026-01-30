---
title: Quick Start Tutorial | Agent SDK
description: Build your first AI agent in under 5 minutes. A simple 'Hello World' tutorial for the Agent SDK using OpenAI or Gemini.
keywords: 
    - quick start
    - tutorial
    - hello world
    - first agent
    - python ai tutorial
    - beginner guide
---

# Quick Start

This guide will get you up and running with a simple AI agent in minutes.

## 1. Setup API Keys

Create a `.env` file in your project root and add your API keys:

```ini
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant...
```

## 2. Create Your First Agent

Here is a simple example using OpenRouter (which supports many models). You can replace `OpenRouterClient` with `OpenAIClient`, `GeminiClient`, etc.

```python
import os
from dotenv import load_dotenv
from agent_sdk import Runner, Agent, OpenRouterClient

# 1. Load Environment Variables
load_dotenv()

# 2. Initialize Client and Runner
client = OpenRouterClient(api_key=os.getenv("OPENRouter_API_KEY"))
runner = Runner(client)

# 3. Define the Agent
assistant = Agent(
    name="Assistant",
    model="mistralai/mistral-7b-instruct",
    instructions="You are a helpful assistant who answers concisely."
)

# 4. Run the Agent (Streaming)
print(f"Chatting with {assistant.name}...
")
stream = runner.run_stream(assistant, "Hello! Who are you?")

for event in stream:
    if event.type == "token":
        print(event.data, end="", flush=True)
    elif event.type == "final":
        print("\n\n[Done]")
```

## 3. What Just Happened?

1.  **Client:** We initialized a client to communicate with the LLM provider.
2.  **Runner:** The `Runner` class manages the conversation loop, tool execution, and memory.
3.  **Agent:** We defined an `Agent` with a name, a specific model, and system instructions.
4.  **Streaming:** `runner.run_stream` returns a generator that yields events (tokens, tool calls, errors) in real-time.

## Next Steps

- Learn about [Universal Clients](../modules/clients.md) to use different providers.
- Explore [Agents & Runners](../modules/agents.md) for more configuration options.
- Add [Tools](../modules/tools.md) to give your agent capabilities like web search or file access.