import unittest
from agent_sdk import Agent, Runner, BaseClient, AgentStreamEvent
from typing import List, Dict, Any, Generator, AsyncGenerator

# Mock Client (Gerçek API'ye gitmez)
class MockClient(BaseClient):
    def chat(self, model, messages, **kwargs):
        return {"content": "Mock Response", "raw": {}}
    
    async def chat_async(self, model, messages, **kwargs):
        return {"content": "Mock Async Response", "raw": {}}
    
    def chat_stream(self, model, messages, **kwargs):
        # agent_name argümanı eklendi
        yield AgentStreamEvent("token", "Mock ", "TestBot")
        yield AgentStreamEvent("token", "Stream", "TestBot")
        yield AgentStreamEvent("final", None, "TestBot")

    async def chat_stream_async(self, model, messages, **kwargs):
        yield AgentStreamEvent("token", "Mock ", "TestBot")
        yield AgentStreamEvent("token", "Async", "TestBot")
        yield AgentStreamEvent("final", None, "TestBot")

class TestCore(unittest.TestCase):
    def test_agent_initialization(self):
        agent = Agent(name="TestBot", model="gpt-4", instructions="Be helpful.")
        self.assertEqual(agent.name, "TestBot")
        # Agent otomatik prefix ekliyor, assertion'ı buna göre güncelledik
        self.assertIn("You are an AI agent named TestBot.", agent.system_prompt())
        self.assertIn("Be helpful.", agent.system_prompt())

    def test_runner_sync(self):
        client = MockClient()
        runner = Runner(client)
        agent = Agent(name="TestBot", model="gpt-4")
        
        stream = runner.run_stream(agent, "Hello")
        content = ""
        for event in stream:
            if event.type == "token":
                content += str(event.data)
        
        self.assertEqual(content, "Mock Stream")

if __name__ == "__main__":
    unittest.main()
