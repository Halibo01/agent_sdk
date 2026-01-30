---
title: Introduction | Agent SDK
description: Welcome to the Agent SDK documentation. Learn how to build, deploy, and manage intelligent AI agents and swarms using Python.
keywords: 
    - agent sdk
    - python ai framework
    - llm agents
    - multi-agent systems
    - introduction
---

# Introduction to Agent SDK

Welcome to the **Agent SDK**, a lightweight, zero-dependency Python framework designed for building intelligent LLM Agents and Multi-Agent Swarms.

Whether you are building a simple chatbot, a complex research assistant, or an autonomous swarm of agents working together, Agent SDK provides the primitives you need without the bloat.

## Why Agent SDK?

*   **Lightweight & Fast**: No heavy dependencies. Pure Python.
*   **Model Agnostic**: Works with OpenAI, Gemini, Anthropic, Ollama, and more.
*   **Middleware First**: Easily add capabilities like Memory (RAG), Safety, and Logging via a robust middleware system.
*   **Swarm Ready**: Built-in support for multi-agent collaboration and handoffs (`AgentSwarm`).

## Core Concepts

*   **[Agents](./modules/agents.md)**: The brain of your application. An Agent wraps an LLM with specific instructions and tools.
*   **[Runners](./modules/agents.md)**: The runtime environment that executes the Agent's reasoning loop.
*   **[Tools](./modules/tools.md)**: Functions that Agents can call to interact with the real world (APIs, File System, etc.).
*   **[Middleware](./modules/middlewares/index.md)**: Plugins that intercept and modify the Agent's behavior (e.g., adding long-term memory).

## Getting Started

Ready to build?

1.  **[Installation](./getting-started/installation.md)**: Set up your environment.
2.  **[Quick Start](./getting-started/quickstart.md)**: Build your first agent in 5 minutes.
3.  **[Examples](https://github.com/Halibo01/agent_sdk/tree/main/examples)**: Check out real-world usage patterns.

## Community

*   [GitHub Repository](https://github.com/Halibo01/agent_sdk)
*   [Report a Bug](https://github.com/Halibo01/agent_sdk/issues)

---
<div class="grid cards" markdown>

-   :material-clock-fast: **Quick Start**
    ---
    Get up and running with a simple agent in seconds.
    [:arrow_right: Go to Quick Start](./getting-started/quickstart.md)

-   :material-robot: **Agents & Tools**
    ---
    Dive deep into creating powerful agents with custom tools.
    [:arrow_right: Learn about Agents](./modules/agents.md)

-   :material-layers-triple: **Middleware**
    ---
    Enhance your agents with RAG, Safety checks, and Logging.
    [:arrow_right: Explore Middleware](./modules/middlewares/index.md)

-   :material-hive: **Swarm Architecture**
    ---
    Connect multiple agents into a collaborative mesh network.
    [:arrow_right: Build a Swarm](./advanced/swarm.md)

</div>
