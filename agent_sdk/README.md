OpenRouter SDK (minimal)

This folder provides a tiny synchronous client to call OpenRouter's chat completions.

Install runtime dependency:

```bash
pip install requests
```

Quick example:

```python
from openrouter_sdk import OpenRouterClient

client = OpenRouterClient(api_key="YOUR_API_KEY")
resp = client.chat_completion(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":"Hello from OpenRouter SDK"}],
)
print(resp)
```

Files:

- `client.py` — `OpenRouterClient` implementation
- `example_usage.py` — tiny runnable example

Streaming and tools

The SDK supports streaming tokens and a minimal tool orchestration helper.

Example (streaming):

```python
from openrouter_sdk import OpenRouterClient
client = OpenRouterClient(api_key="YOUR_API_KEY")
for token in client.chat_stream(model="gpt-4o-mini", messages=[{"role":"user","content":"Hello"}]):
    print(token, end="")
```

Register a tool and use `chat_with_tools` to handle function calls automatically:

```python
def my_tool(input_str):
    return "tool-output"

client.register_tool("tool_name", my_tool)
resp = client.chat_with_tools(model="gpt-4o-mini", messages=[{"role":"user","content":"Call tool_name please."}])
print(resp)
```
