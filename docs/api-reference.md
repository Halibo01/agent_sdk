# API Reference

## Agent
`agent_sdk.agent.Agent`

## Runner
`agent_sdk.runner.Runner`

## Clients
*   `agent_sdk.clients.openai.OpenAIClient`
*   `agent_sdk.clients.gemini.GeminiClient`
*   `agent_sdk.clients.anthropic.AnthropicClient`
*   `agent_sdk.clients.ollama.OllamaClient`

## Middleware
`agent_sdk.middleware.base.Middleware`

*   `agent_sdk.middleware.approval.HumanInTheLoop`
*   `agent_sdk.middleware.logger.FileLogger`
*   `agent_sdk.middleware.rag.SimpleRAG`
*   `agent_sdk.middleware.rag.ChromaRAG`

## Tools
`agent_sdk.tools`

*   `@tool_message(template)`
*   `@approval_required`