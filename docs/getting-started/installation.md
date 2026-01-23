# Installation

## Prerequisites

- Python 3.9 or higher.
- API keys for your preferred LLM providers (e.g., OpenAI, Gemini, Anthropic).

## Install via Pip

You can install the core package easily via pip:

```bash
pip install agent-sdk-core
```

## Optional Dependencies

The SDK allows you to install only what you need.

| Feature | Command | Description |
| :--- | :--- | :--- |
| **OpenAI Support** | `pip install agent-sdk-core[openai]` | Adds support for OpenAI models. |
| **Gemini Support** | `pip install agent-sdk-core[gemini]` | Adds support for Google Gemini models. |
| **RAG (ChromaDB)** | `pip install agent-sdk-core[rag]` | Adds ChromaDB support for vector-based RAG. |
| **Tools** | `pip install agent-sdk-core[tools]` | Adds extra dependencies for tools (e.g., duckduckgo-search, wikipedia). |
| **All Features** | `pip install agent-sdk-core[all]` | Installs everything. |

## Development Setup

If you want to contribute or modify the source code:

```bash
git clone https://github.com/Halibo01/agent_sdk.git
cd agent_sdk
pip install -e .[all]
```