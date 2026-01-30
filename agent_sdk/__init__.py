"""
Agent SDK Core Library

A powerful SDK for building and managing AI agents, swarms, and tools.

Documentation: https://docs.agent-sdk-core.dev/
Repository: https://github.com/Halibo01/agent_sdk

Features:
- **Universal Client Support:** OpenAI, Gemini, Anthropic, Ollama, DeepSeek, and more.
- **Agent Swarms:** Collaborative multi-agent systems.
- **Middleware:** RAG, Human-in-the-Loop, Logging, Reflection.
- **Hybrid Async/Sync:** Seamless support for both execution modes.
- **Advanced Tooling:** Sandboxed code execution, web search, and file operations.

Installation:
    pip install agent-sdk-core

Basic Usage:
    >>> from agent_sdk import Agent, Runner, OpenAIClient
    >>> client = OpenAIClient(api_key="sk-...")
    >>> runner = Runner(client)
    >>> agent = Agent(name="Bot", instructions="You are helpful.")
    >>> runner.run_stream(agent, "Hello!")
"""

# Clients
from .clients.base import BaseClient
from .clients.openrouter import OpenRouterClient
from .clients.ollama import OllamaClient
from .clients.openai import OpenAIClient, GrokClient, DeepSeekClient, QwenClient, ZhipuClient
from .clients.anthropic import AnthropicClient
from .clients.gemini import GeminiClient

# Core
from .runner import Runner
from .agent import Agent
from .swarm import AgentSwarm
from .bridge import AgentBridge
from .events import AgentStreamEvent
from .decorators import tool_message, approval_required
from .sandbox import LocalSandbox, DockerSandbox

# Tools
from .tools import (
    get_current_time,
    web_search,
    wikipedia_search,
    list_directory,
    read_file,
    execute_command,
    run_python_code,
    list_directory_async,
    read_file_async,
    execute_command_async,
    run_python_code_async,
    LangSearch,
    VisitWebpage,
    save_file
)

__version__ = "0.1.6"


__all__ = [
    # Clients
    "BaseClient",
    "OpenRouterClient",
    "OllamaClient",
    "OpenAIClient",
    "GrokClient",
    "DeepSeekClient",
    "QwenClient",
    "ZhipuClient",
    "AnthropicClient",
    "GeminiClient",
    
    # Core
    "Runner",
    "Agent",
    "AgentSwarm",
    "AgentBridge",
    "AgentStreamEvent",
    "tool_message",
    "approval_required",
    "LocalSandbox",
    "DockerSandbox",
    
    # Tools
    "get_current_time",
    "web_search",
    "wikipedia_search",
    "list_directory",
    "read_file",
    "execute_command",
    "run_python_code",
    "list_directory_async",
    "read_file_async",
    "execute_command_async",
    "run_python_code_async",
    "LangSearch",
    "VisitWebpage",
    "save_file",
]