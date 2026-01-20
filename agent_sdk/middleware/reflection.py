from .base import Middleware
from agent_sdk.agent import Agent
import json

class SelfReflection(Middleware):
    def __init__(self, model: str = "mistralai/devstral-2512:free"):
        self.model = model

    def _analyze_response(self, agent: Agent, runner, last_message: str):
        """
        Ajanın cevabını analiz eder.
        """
        # Kullanıcının son isteği
        user_req = "Unknown"
        for msg in reversed(agent.memory[:-1]):
            if msg["role"] == "user":
                user_req = msg["content"]
                break

        prompt = [
            {"role": "system", "content": "You are a critical AI supervisor. Your job is to check if the assistant's response is safe, correct, and helpful."},
            {"role": "user", "content": f"""
            USER REQUEST: {user_req}
            
            ASSISTANT RESPONSE: {last_message}
            
            Evaluate the assistant's response. 
            If it is good, reply with "OK".
            If it has errors (bugs, security risks, hallucinations, or didn't answer the question), reply with "CRITICISM: [Explain the error clearly]".
            """}
        ]

        try:
            # Sync analiz
            response = runner.client.chat(model=self.model, messages=prompt)
            return response["content"]
        except Exception as e:
            print(f"[Reflection] Hata: {e}")
            return "OK"

    async def _analyze_response_async(self, agent: Agent, runner, last_message: str):
        """
        Async analiz.
        """
        user_req = "Unknown"
        for msg in reversed(agent.memory[:-1]):
            if msg["role"] == "user":
                user_req = msg["content"]
                break

        prompt = [
            {"role": "system", "content": "You are a critical AI supervisor."},
            {"role": "user", "content": f"USER: {user_req}\nAI: {last_message}\nEvaluate. Reply 'OK' or 'CRITICISM: [Reason]'."}
        ]

        try:
            response = await runner.client.chat_async(model=self.model, messages=prompt)
            return response["content"]
        except Exception as e:
            print(f"[Reflection] Hata: {e}")
            return "OK"

    def after_run(self, agent: Agent, runner):
        # Sadece Assistant mesajlarını kontrol et
        if not agent.memory: return
        last_msg = agent.memory[-1] 
        
        if last_msg.get("role") != "assistant" or not last_msg.get("content"):
            return

        evaluation = self._analyze_response(agent, runner, last_msg["content"])
        
        if evaluation.startswith("CRITICISM:"):
            feedback = evaluation.replace("CRITICISM:", "").strip()
            print(f"\n{Agent.COLOR_Reviewer if hasattr(Agent, 'COLOR_Reviewer') else ''}[Self-Reflection] Müdahale: {feedback}")
            
            # Hafızaya eleştiriyi ekle
            agent.memory.append({
                "role": "user", # User rolüyle ekliyoruz ki ajan dikkate alsın
                "content": f"[SYSTEM FEEDBACK]: Your previous answer has issues: {feedback}. Please fix it and respond again."
            })
            # Not: Burada runner'ı tekrar tetiklemek için bir mekanizma yok. 
            # Ancak bir sonraki turda ajan bunu görecek. 
            # Otomatik loop için runner yapısının değişmesi gerekir.

    async def after_run_async(self, agent: Agent, runner):
        if not agent.memory: return
        last_msg = agent.memory[-1]
        
        if last_msg.get("role") != "assistant" or not last_msg.get("content"):
            return

        evaluation = await self._analyze_response_async(agent, runner, last_msg["content"])
        
        if evaluation.startswith("CRITICISM:"):
            feedback = evaluation.replace("CRITICISM:", "").strip()
            print(f"\n[Self-Reflection] Müdahale: {feedback}")
            
            agent.memory.append({
                "role": "user",
                "content": f"[SYSTEM FEEDBACK]: Your previous answer has issues: {feedback}. Please fix it."
            })