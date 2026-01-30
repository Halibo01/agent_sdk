"""
Swarm Module

Facilitates multi-agent collaboration by creating a mesh network of agents.
The `AgentSwarm` allows agents to discover and call each other as tools.

Documentation: https://docs.agent-sdk-core.dev/advanced/swarm
"""

from typing import List, Dict, Callable, Optional
from .agent import Agent
from .runner import Runner
from .bridge import AgentBridge
from .events import AgentStreamEvent

class AgentSwarm:
    def __init__(self, runner: Runner, event_handler: Optional[Callable[[AgentStreamEvent], None]] = None):
        """
        Agent Swarm manager.

        Args:
            runner: Engine that will run the Agents.
            event_handler: Callback function to forward events produced by
                           sub-agents (token, reasoning, tool_call) to the main flow.
        """
        self.runner = runner
        self.event_handler = event_handler
        self.agents: List[Agent] = []
        self.bridges: Dict[str, Callable] = {}

    def add_agent(self, agent: Agent):
        """Add an agent to the swarm (does not connect tools yet)."""
        self.agents.append(agent)

    def connect_all(self):
        """
        Build a fully connected mesh network:
        1. Create an AgentBridge tool for each agent.
        2. Distribute these tools to all other agents (except the owner).
        3. This allows every agent to communicate with every other agent.
        """
        print("--- Building Swarm Network ---")
        
        # 1. STEP: Create bridges
        for agent in self.agents:
            
            # Is there a custom 'handoff_msg' defined on the agent?
            # (This may be an attribute added to the Agent class later.)
            handoff_template = getattr(agent, "handoff_msg", None)
            
            # Configure the bridge
            bridge = AgentBridge(
                agent=agent, 
                runner=self.runner, 
                on_event=self.event_handler,    # <--- Event Tunneling
                handoff_template=handoff_template # <--- Custom Message Template
            )
            
            # Produce the tool (get the function)
            tool = bridge.create_tool()
            
            # Use the tool's __name__ as the key
            # In AgentBridge this name is set to "ask_{agent_name}".
            self.bridges[tool.__name__] = tool
            
            # Optional info
            # print(f"✅ Bridge created: {tool.__name__}")

        # 2. STEP: Distribute tools (wiring)
        for agent in self.agents:
            # Preserve agent's existing tools (if any) and add to them
            if agent.tools is None:
                agent.tools = {}
            
            current_tools = agent.tools.copy()
            
            # Exclude tools that match the agent's own name
            # (prevents infinite self-calls)
            my_tool_name = f"ask_{agent.name.lower().replace(' ', '_')}"
            
            peer_tools = {
                name: tool 
                for name, tool in self.bridges.items() 
                if name != my_tool_name
            }
            
            # Add peer agent tools into this agent's tools
            current_tools.update(peer_tools)
            agent.tools = current_tools
            
            # print(f"🔗 {agent.name} can now access agents: {list(peer_tools.keys())}")
            
        print("--- All agents connected ---")

    def connect_all_async(self):
        """
        Asynchronous fully connected network setup.
        Same logic as 'connect_all' but produces async tools instead of sync.
        """
        print("--- Building Swarm Network (Async) ---")
        
        for agent in self.agents:
            handoff_template = getattr(agent, "handoff_msg", None)
            bridge = AgentBridge(
                agent=agent, 
                runner=self.runner, 
                on_event=self.event_handler,
                handoff_template=handoff_template
            )
            
            # ASYNC TOOL ÜRET
            tool = bridge.create_async_tool()
            self.bridges[tool.__name__] = tool

        for agent in self.agents:
            if agent.tools is None:
                agent.tools = {}
            
            current_tools = agent.tools.copy()
            my_tool_name = f"ask_{agent.name.lower().replace(' ', '_')}"
            
            peer_tools = {
                name: tool 
                for name, tool in self.bridges.items() 
                if name != my_tool_name
            }
            
            current_tools.update(peer_tools)
            agent.tools = current_tools
            
        print("--- All agents connected (Async) ---")