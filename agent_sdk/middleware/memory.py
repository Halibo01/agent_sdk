from .base import Middleware
from agent_sdk.agent import Agent

class MemorySummarizer(Middleware):
    def __init__(self, threshold: int = 15, keep_last: int = 5, model: str = "mistralai/devstral-2512:free"):
        self.threshold = threshold
        self.keep_last = keep_last
        self.model = model

    def _prepare_summary_data(self, agent: Agent):
        """
        Prepare data required for summarization.
        Return: (system_prompt, recent_context, prompt_messages) or None
        """
        if len(agent.memory) <= self.threshold:
            return None

        print(f"\n[MemorySummarizer] {agent.name} memory near threshold ({len(agent.memory)}/{self.threshold}). Summarizing...")

        system_prompt = agent.memory[0] if agent.memory else None
        to_summarize = agent.memory[1 : -self.keep_last]
        recent_context = agent.memory[-self.keep_last:]

        if not to_summarize:
            return None

        conversation_text = ""
        for msg in to_summarize:
            role = msg.get("role", "unknown")
            content = msg.get("content") or ""
            conversation_text += f"{role.upper()}: {content}\n"

        prompt_messages = [
            {"role": "system", "content": "You are a generic assistant."},
            {"role": "user", "content": f"Summarize the conversation below into a single concise paragraph. Keep key facts.\n\n{conversation_text}"}
        ]
        
        return system_prompt, recent_context, prompt_messages

    def _apply_summary(self, agent: Agent, summary_text: str, system_prompt, recent_context):
        """Apply the summary text into memory."""
        new_memory = []
        if system_prompt:
            new_memory.append(system_prompt)
        
        new_memory.append({
            "role": "system", 
            "content": f"[SYSTEM: Previous conversation summary]: {summary_text}"
        })
        
        new_memory.extend(recent_context)
        agent.memory = new_memory
        print(f"[MemorySummarizer] Memory compacted. New size: {len(agent.memory)}")

    def before_run(self, agent: Agent, runner):
        """Synchronous version"""
        data = self._prepare_summary_data(agent)
        if not data: return

        system_prompt, recent_context, prompt_messages = data

        try:
            response = runner.client.chat(
                model=self.model,
                messages=prompt_messages
            )
            self._apply_summary(agent, response["content"], system_prompt, recent_context)
        except Exception as e:
            print(f"[MemorySummarizer] Summarization error: {e}")

    async def before_run_async(self, agent: Agent, runner):
        """Asynchronous version"""
        data = self._prepare_summary_data(agent)
        if not data: return

        system_prompt, recent_context, prompt_messages = data

        try:
            # Asynchronous call
            response = await runner.client.chat_async(
                model=self.model,
                messages=prompt_messages
            )
            self._apply_summary(agent, response["content"], system_prompt, recent_context)
        except Exception as e:
            print(f"[MemorySummarizer] Summarization error: {e}")