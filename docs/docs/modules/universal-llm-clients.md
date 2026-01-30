---
title: Universal LLM Clients | Agent SDK
description: Connect to OpenAI, Google Gemini, Anthropic Claude, Ollama, and more using a unified Client API. Switch models without changing code.
keywords: 
    - llm client
    - openai client
    - gemini client
    - anthropic client
    - ollama integration
    - model agnostic
    - python llm wrapper
---

# Universal Clients

Agent SDK provides a unified interface for various LLM providers. You can switch between providers by simply changing the client class.

## Supported Clients

| Client Class | Provider | Description |
| :--- | :--- | :--- |
| `OpenAIClient` | OpenAI | Supports GPT-4o, GPT-3.5 Turbo, and compatible APIs (e.g., DeepSeek, Grok). |
| `GeminiClient` | Google | Supports Gemini 1.5 Pro, Flash, etc. |
| `AnthropicClient` | Anthropic | Supports Claude 3.5 Sonnet, Opus, Haiku. |
| `OpenRouterClient` | OpenRouter | Unified access to almost all open and closed models. |
| `OllamaClient` | Ollama | For running local models (Llama 3, Mistral, etc.). |
| `DeepSeekClient` | DeepSeek | Specialized client for DeepSeek V3 and R1. |

## Usage Examples

### OpenAI

```python
from agent_sdk import OpenAIClient

client = OpenAIClient(api_key="sk-...")
```

### Google Gemini

```python
from agent_sdk import GeminiClient

client = GeminiClient(api_key="AIza...")
```

### Local Models (Ollama)

```python
from agent_sdk import OllamaClient

# Default base_url is http://localhost:11434
client = OllamaClient(base_url="http://localhost:11434")
```

## Direct Chat Usage (No Agent)

You can use clients directly without the Agent/Runner abstraction if you just need a simple chat completion.

### Synchronous Chat

```python
messages = [{"role": "user", "content": "Explain quantum physics."}]

# Non-streaming
response = client.chat(model="gpt-4o", messages=messages)
print(response["content"])

# Streaming
stream = client.chat_stream(model="gpt-4o", messages=messages)
for event in stream:
    print(event.data, end="")
```

### Asynchronous Chat

```python
import asyncio

async def main():
    stream = client.chat_stream_async(model="gpt-4o", messages=messages)
    async for event in stream:
        print(event.data, end="")

asyncio.run(main())
```