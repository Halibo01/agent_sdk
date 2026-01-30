---
title: Building Custom Middleware | Agent SDK
description: Learn how to extend the Agent SDK by creating custom middleware. Intercept agent actions, integrate APIs, and build custom logic like billing or monitoring.
keywords: 
    - custom middleware
    - extending agent sdk
    - python middleware
    - agent hooks
    - interceptors
    - plugin system
---

# Custom Middleware

The `agent_sdk` is designed to be extensible. You can create your own middleware to integrate with custom APIs, monitoring tools, or proprietary logic.

All middleware must inherit from the `Middleware` base class.

## The Middleware Interface

```python
from agent_sdk.middleware.base import Middleware

class MyMiddleware(Middleware):
    
    # --- Sync Hooks ---
    
    def before_run(self, agent, runner):
        """Called before the agent starts its reasoning loop."""
        pass

    def after_run(self, agent, runner):
        """Called after the agent finishes its task."""
        pass

    def before_tool_execution(self, agent, runner, tool_name, tool_args, tool_call_id):
        """
        Called before a tool is executed.
        Return True to allow execution, False to block it.
        """
        return True

    def after_tool_execution(self, agent, runner, tool_name, tool_args, result):
        """Called after a tool has been executed."""
        pass
        
    # --- Async Hooks (Optional) ---
    # If your runner uses .run_async(), implement these:
    
    async def before_run_async(self, agent, runner):
        pass
        
    async def after_run_async(self, agent, runner):
        pass
        
    async def before_tool_execution_async(self, agent, runner, tool_name, tool_args, tool_call_id):
        return True
```

## Example: Billing Middleware

Imagine you want to charge users for every tool execution.

```python
class BillingMiddleware(Middleware):
    def __init__(self, cost_per_tool=0.01):
        self.cost = cost_per_tool

    def before_tool_execution(self, agent, runner, tool_name, tool_args, tool_call_id):
        user_balance = get_user_balance(agent.user_id)
        
        if user_balance < self.cost:
            print(f"Insufficient funds for {agent.user_id}")
            return False # Block execution
            
        deduct_balance(agent.user_id, self.cost)
        print(f"Charged ${self.cost} for using {tool_name}")
        return True
```
