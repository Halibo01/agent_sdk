---
title: Python ile AI Swarm (Sürü) Mimarisi Kurulumu
description: How to build autonomous swarm systems where multiple AI agents (multi-agents) communicate with each other using the Agent SDK?
keywords: 
    - multi-agent systems
    - python swarm
    - otonom ajanlar
    - ai swarm
    - mesh system
    - mesh-agents
    - agent systems
---

# Swarm & Handoffs

Agent SDK supports multi-agent collaboration, allowing specialized agents to work together.

## Agent Bridge

The `AgentBridge` allows one agent to call another agent as if it were a tool.

**Scenario:** A "Manager" agent delegates a coding task to a "Coder" agent.

```python
from agent_sdk import Agent, Runner, AgentBridge

# 1. Define Agents
manager = Agent(name="Manager", instructions="Plan the task and delegate technical work.")
coder = Agent(name="Coder", instructions="Write and execute Python code.")

# 2. Bridge Coder to Manager
# This creates a tool named 'ask_coder(task: str)' and gives it to the Manager.
bridge = AgentBridge(agent=coder, runner=runner)
manager.tools["ask_coder"] = bridge.create_tool()

# 3. Run Manager
runner.run_stream(manager, "Create a snake game in Python.")
```

**Flow:**
1. Manager receives request.
2. Manager calls `ask_coder("Create a snake game...")`.
3. Coder receives the message, does the work, and returns the result string.
4. Manager receives the result and reports back to the user.

## Agent Swarm

The `AgentSwarm` creates a **mesh network** where every agent is connected to every other agent automatically.

```python
from agent_sdk import AgentSwarm

swarm = AgentSwarm(runner)
swarm.add_agent(manager)
swarm.add_agent(coder)
swarm.add_agent(researcher)

# Connects everyone to everyone
swarm.connect_all() 

# Start with any agent
runner.run_stream(manager, "Research the market and build a prototype.")
```

## Handoffs (Transferring Control)

Instead of a sub-call (function call style), an agent can "handoff" the conversation entirely to another agent.

*Note: Handoff logic is typically handled by setting a specific return value or flag that the loop detects to switch the active `agent_stack`.* 

(Currently, `AgentBridge` is the primary method for interaction, functioning as a sub-routine call.)