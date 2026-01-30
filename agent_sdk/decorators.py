"""
Decorators Module

Helper decorators for defining and enhancing tools.
- `@tool_message`: Sets a custom status message for tool execution.
- `@approval_required`: Marks a tool as requiring human approval (middleware).

Documentation: https://docs.agent-sdk-core.dev/modules/tools
"""

import functools
import inspect

def tool_message(template: str):
    """
    Decorator to attach a UI message template to tool functions.
    E.g.: @tool_message("Coder is taking over for {task}...")
    Supports both synchronous and asynchronous functions.
    """
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            async_wrapper._message_template = template
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            sync_wrapper._message_template = template
            return sync_wrapper
    return decorator

def approval_required(func):
    """
    Mark a tool as requiring human approval before execution.
    HumanInTheLoop middleware checks for this marker.
    Supports both synchronous and asynchronous functions.
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        async_wrapper._approval_required = True
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        sync_wrapper._approval_required = True
        return sync_wrapper