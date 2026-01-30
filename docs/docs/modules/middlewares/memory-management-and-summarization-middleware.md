---
title: Memory Management & Summarization | Agent SDK
description: Manage AI agent context windows efficiently with MemorySummarizer. Automatically summarize long conversations to save tokens and prevent context overflow.
keywords: 
    - memory management
    - context window
    - conversation summary
    - agent memory
    - token optimization
    - infinite conversation
---

# Memory Management

Agents have a limited "context window" (the amount of text they can remember at once). As conversations grow, they can hit this limit, causing errors or forgetting earlier instructions.

The `MemorySummarizer` middleware solves this by automatically compressing old messages into a concise summary while keeping the most recent messages intact.

---

## MemorySummarizer

This middleware monitors the number of messages in the agent's history. When it exceeds a defined `threshold`, it triggers a summarization process.

### Strategy
It uses a **"Rolling Window + Summary"** approach:
1.  **System Prompt**: Always preserved at index 0.
2.  **Summary**: Old conversation history is compressed into a single `System` message.
3.  **Recent Context**: The last `N` messages are kept verbatim to maintain conversational flow.

### Usage

```python
from agent_sdk.middleware import MemorySummarizer

summarizer = MemorySummarizer(
    threshold=15,    # Trigger summary when messages > 15
    keep_last=5,     # Keep the last 5 messages raw
    model="gemini-2.0-flash" # Model to perform the summarization
)

runner.use(summarizer)
```

### Flow
1.  **Check**: Before every run, it checks `len(agent.memory)`.
2.  **Trigger**: If `len > threshold`, it takes the middle chunk of messages.
3.  **Summarize**: Calls the LLM to summarize that chunk.
4.  **Replace**: Updates `agent.memory` to be: `[System Prompt, Summary, ...Recent Messages]`.

### Benefits
*   **Infinite Conversations**: Theoretically allows conversations to go on forever without crashing context limits.
*   **Cost Efficiency**: Reduces token usage for long-running sessions.
*   **Focus**: Helps the agent focus on the immediate context while retaining key facts from the past.
