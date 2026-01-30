"""
Bridge Module

The `AgentBridge` wraps an `Agent` as a callable tool, allowing other agents or external 
systems to invoke it with a natural language task. It handles the message passing and 
execution via a `Runner`.

Documentation: https://docs.agent-sdk-core.dev/advanced/swarm
"""

from typing import Callable, Optional
from .agent import Agent
from .runner import Runner 
from .events import AgentStreamEvent
from .decorators import tool_message

class AgentBridge:
    def __init__(
        self, 
        agent: Agent, 
        runner: Runner, 
        on_event: Optional[Callable[[AgentStreamEvent], None]] = None,
        handoff_template: Optional[str] = None  # <--- NEW PARAMETER
    ):
        """
        Args:
            agent: Target Agent that will be exposed as a Tool.
            runner: Runner engine.
            on_event: Live event callback.
            handoff_template: Custom handoff message template.
                              E.g.: "{task} - our specialist takes over..."
                              If None, a default template is used.
        """
        self.agent = agent
        self.runner = runner
        self.on_event = on_event
        self.handoff_template = handoff_template # store the template

    def create_tool(self) -> Callable:
        
        # 1. TEMPLATE SELECTION LOGIC
        # Use user-provided template if given, otherwise default.
        if self.handoff_template:
            selected_template = self.handoff_template
        else:
            # Default Template
            selected_template = f"{self.agent.name} is stepping in for task: {{task}}..."

        # 2. Provide the selected template to the decorator
        @tool_message(selected_template)
        def ask_agent_wrapper(task: str) -> str:
            """
            Delegates a specific task to this specialized sub-agent.
            """
            # 1. Get sender identity
            sender_name = self.runner.current_sender
            
            # 2. Enrich the message (add who sent it)
            enriched_task = f"[SYSTEM INFO: Incoming request from agent '{sender_name}']\nTASK: {task}"

            full_response_text = ""
            
            # 3. Send the enriched task
            stream = self.runner.run_stream(self.agent, enriched_task)
            
            for event in stream:
                if event.type == "token" and isinstance(event.data, str):
                    full_response_text += event.data
                
                if self.on_event:
                    self.on_event(event)

            return full_response_text

        # 3. Metadata settings (unchanged)
        func_name = f"ask_{self.agent.name.lower().replace(' ', '_')}"
        ask_agent_wrapper.__name__ = func_name
        
        agent_desc = self.agent.instructions[:300].replace("\n", " ")
        ask_agent_wrapper.__doc__ = f"Ask {self.agent.name} to perform a task. Expertise: {agent_desc}..."
        
        return ask_agent_wrapper

    def create_async_tool(self) -> Callable:
        """
        Create an async tool wrapper.
        """
        
        if self.handoff_template:
            selected_template = self.handoff_template
        else:
            selected_template = f"{self.agent.name} is stepping in for task: {{task}}..."

        @tool_message(selected_template)
        async def ask_agent_async_wrapper(task: str) -> str:
            """
            Delegates a specific task to this specialized sub-agent asynchronously.
            """
            sender_name = self.runner.current_sender
            enriched_task = f"[SYSTEM INFO: Incoming request from agent '{sender_name}']\nTASK: {task}"

            full_response_text = ""
            
            # ASYNC STREAM
            stream = self.runner.run_stream_async(self.agent, enriched_task)
            
            async for event in stream:
                if event.type == "token" and isinstance(event.data, str):
                    full_response_text += event.data
                
                if self.on_event:
                    # Note: If event handler is synchronous call directly, otherwise await it.
                    # For simplicity, assume synchronous handlers (print etc.).
                    self.on_event(event)

            return full_response_text

        func_name = f"ask_{self.agent.name.lower().replace(' ', '_')}"
        ask_agent_async_wrapper.__name__ = func_name
        
        agent_desc = self.agent.instructions[:300].replace("\n", " ")
        ask_agent_async_wrapper.__doc__ = f"Ask {self.agent.name} to perform a task. Expertise: {agent_desc}..."
        
        return ask_agent_async_wrapper