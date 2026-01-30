from abc import ABC, abstractmethod

class Middleware(ABC):
    """
    Base class for middleware that intercepts the Agent execution flow.
    Supports both synchronous (run_stream) and asynchronous (run_stream_async) modes.
    """
    
    # --- SYNCHRONOUS HOOKS ---
    def before_run(self, agent, runner):
        """
        Executed immediately before the Agent starts running (run_stream).
        """
        pass

    def after_run(self, agent, runner):
        """
        Executed after the Agent finishes running.
        """
        pass

    def before_tool_execution(self, agent, runner, tool_name: str, tool_args: dict, tool_call_id: str = None) -> bool:
        """
        Triggered when the Agent decides to execute a tool.
        Return True -> Continue, False -> Cancel.
        """
        return True

    def process_stream_event(self, event, agent, runner):
        """
        Intercepts every stream event from the Agent.
        
        Args:
            event: AgentStreamEvent object (token, tool_call, etc.)
            
        Returns:
            List[AgentStreamEvent] or None. 
            If a list is returned, these new events are injected into the stream.
        """
        return None

    # --- ASYNCHRONOUS HOOKS ---
    async def before_run_async(self, agent, runner):
        """
        Called in asynchronous execution (run_stream_async).
        Defaults to calling the synchronous version (beware of blocking).
        Override to implement async logic.
        """
        self.before_run(agent, runner)

    async def after_run_async(self, agent, runner):
        """
        Called in asynchronous execution (run_stream_async).
        """
        self.after_run(agent, runner)

    async def before_tool_execution_async(self, agent, runner, tool_name: str, tool_args: dict, tool_call_id: str = None) -> bool:
        """
        Called in asynchronous execution (run_stream_async).
        Return True -> Continue, False -> Cancel.
        """
        return self.before_tool_execution(agent, runner, tool_name, tool_args, tool_call_id)

    async def process_stream_event_async(self, event, agent, runner):
        """
        Called for every event during async stream.
        """
        return self.process_stream_event(event, agent, runner)