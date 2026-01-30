---
title: Safety & Control Middlewares | Agent SDK
description: Ensure AI safety with HumanInTheLoop and SelfReflection middlewares. Control tool execution and validate agent responses.
keywords: 
    - ai safety
    - human in the loop
    - agent control
    - self reflection
    - ai supervision
    - tool approval
---

# Safety & Control Middlewares

These middlewares ensure your agent operates safely, follows instructions, and allows for human oversight before executing critical actions.

---

## HumanInTheLoop

This middleware pauses execution before a tool is used, allowing a human to approve, reject, or modify the action. It is essential for agents that have access to sensitive tools (e.g., file system write access, API calls, database deletion).

### Usage

#### 1. Console-Based Approval (CLI)
By default, it prompts the user in the terminal.

```python
from agent_sdk.middleware import HumanInTheLoop

# Simple usage for CLI apps
runner.use(HumanInTheLoop())
```

**Interaction:**
```text
🛑 HUMAN APPROVAL REQUIRED 🛑
Agent 'DevBot' wants to execute:
Tool: write_file
Args: {"file_path": "main.py", "content": "..."}

Options:
  [y]es    : Approve
  [n]o     : Deny
  [a]lways : Approve 'write_file' for this session
Choice? (y/n/a):
```

#### 2. Custom Approval Callback
For web applications or APIs, you can provide a custom callback function.

```python
def my_approval_callback(agent_name, tool_name, args, tool_call_id):
    # Logic to send a notification to a UI or wait for a webhook
    # Return values: "approve", "reject", "allow_always"
    
    if tool_name == "delete_user":
        return "reject"
    
    return "approve"

runner.use(HumanInTheLoop(approval_callback=my_approval_callback))
```

### Configuration
*   `always_approve_for_debug` (bool): If `True`, bypasses all checks (dangerous!).
*   `approval_callback`: A function that returns decision strings.

---

## SelfReflection

`SelfReflection` acts as a "Critic" or "Supervisor" that reviews the agent's response *after* it generates an answer but *before* the loop finishes (conceptually). 

*Note: In the current implementation, it reviews the final response and appends feedback to the memory for the **next** turn, forcing the agent to correct itself if the loop continues.*

### How it works
1.  The agent generates a response.
2.  The middleware sends this response + the user's original request to a secondary LLM call.
3.  The secondary model evaluates if the response is safe, correct, and helpful.
4.  If issues are found (e.g., hallucinations, refused to answer), it injects a `[SYSTEM FEEDBACK]` message into the memory.

### Usage

```python
from agent_sdk.middleware import SelfReflection

# Uses a separate model for criticism (optional)
reflection = SelfReflection(model="mistralai/mistral-large-latest")

runner.use(reflection)
```

**Example Scenario:**
1.  **User**: "Write a poem about hacking."
2.  **Agent**: "Here is a poem about breaking into servers..."
3.  **SelfReflection**: Analyzes the response.
4.  **Action**: Detects safety violation. Appends feedback: `[SYSTEM FEEDBACK]: The previous response promotes illegal activity. Please apologize and refuse.`
5.  **Agent (Next Turn)**: "I apologize, I cannot fulfill that request."
