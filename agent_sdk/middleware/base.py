from abc import ABC, abstractmethod

class Middleware(ABC):
    """
    Agent çalışma akışına müdahale eden ara katman sınıfı.
    Hem senkron (run_stream) hem de asenkron (run_stream_async) modları destekler.
    """
    
    # --- SYNCHRONOUS HOOKS ---
    def before_run(self, agent, runner):
        """
        Agent çalışmaya başlamadan (run_stream) hemen önce çalışır.
        """
        pass

    def after_run(self, agent, runner):
        """
        Agent çalışması bittikten sonra çalışır.
        """
        pass

    def before_tool_execution(self, agent, runner, tool_name: str, tool_args: dict, tool_call_id: str = None) -> bool:
        """
        Agent bir tool çalıştırmaya karar verdiğinde tetiklenir.
        Return True -> Devam, False -> İptal.
        """
        return True

    # --- ASYNCHRONOUS HOOKS ---
    async def before_run_async(self, agent, runner):
        """
        Asenkron çalışmada (run_stream_async) çağrılır.
        Varsayılan olarak senkron versiyonu çağırır (bloklayıcı olabilir, dikkat).
        Override ederek 'await' içerecek şekilde yazabilirsiniz.
        """
        self.before_run(agent, runner)

    async def after_run_async(self, agent, runner):
        """
        Asenkron çalışmada (run_stream_async) çağrılır.
        """
        self.after_run(agent, runner)

    async def before_tool_execution_async(self, agent, runner, tool_name: str, tool_args: dict, tool_call_id: str = None) -> bool:
        """
        Asenkron çalışmada (run_stream_async) çağrılır.
        Return True -> Devam, False -> İptal.
        """
        return self.before_tool_execution(agent, runner, tool_name, tool_args, tool_call_id)