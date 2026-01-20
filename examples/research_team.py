"""
Research Team Example (Swarm Architecture)
------------------------------------------
This example demonstrates how to create a multi-agent system (Swarm) where agents 
can collaborate and delegate tasks to each other naturally.

Architecture:
    [Manager] <---> [Researcher]
        ^
        |
    [Writer]

Scenario:
    User asks Manager to write a blog post.
    Manager delegates research to Researcher.
    Manager delegates writing to Writer.
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_sdk import Runner, Agent, AgentSwarm, OpenRouterClient
from agent_sdk.tools import web_search, get_current_time

load_dotenv()

def main():
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENROUTER_API_KEY in .env")
        return

    client = OpenRouterClient(api_key=api_key)
    runner = Runner(client)

    # --- 1. Define Agents ---

    # Agent 1: Researcher (Equipped with search tools)
    researcher = Agent(
        name="Researcher",
        model="mistralai/mistral-7b-instruct",
        instructions="""
        You are a web researcher. 
        1. Search for information when asked.
        2. Summarize your findings concisely.
        """,
        tools={"web_search": web_search, "time": get_current_time}
    )

    # Agent 2: Writer (Pure text generation)
    writer = Agent(
        name="Writer",
        model="mistralai/mistral-7b-instruct",
        instructions="""
        You are a blog post writer. 
        1. Take the information provided by others.
        2. Write a professional, engaging blog post.
        3. Do not search the web yourself.
        """
    )

    # Agent 3: Manager (Orchestrator)
    manager = Agent(
        name="Manager",
        model="mistralai/mistral-7b-instruct",
        instructions="""
        You are the Project Manager.
        1. Receive the user's request.
        2. Ask 'Researcher' to find information.
        3. Pass that information to 'Writer' to create the content.
        4. Review the final result and present it to the user.
        """
    )

    # --- 2. Create Swarm & Connect ---
    
    swarm = AgentSwarm(runner)
    swarm.add_agent(manager)
    swarm.add_agent(researcher)
    swarm.add_agent(writer)
    
    # Automatically creates "ask_Researcher", "ask_Writer", "ask_Manager" tools
    # and distributes them so everyone can talk to everyone.
    swarm.connect_all() 

    print("🔗 Swarm connected. Agents: Manager, Researcher, Writer.")
    
    # --- 3. Run Task ---
    
    task = "Write a short blog post about the latest trends in AI Agents for 2025."
    print(f"\nUser Task: {task}\n")
    print("-" * 40)

    # Start the process with the Manager
    stream = runner.run_stream(manager, task)

    for event in stream:
        if event.type == "token":
            print(event.data, end="", flush=True)
        
        elif event.type == "tool_call_ready":
            # Visualize delegation
            func = event.data[0]['function']
            name = func['name']
            if name.startswith("ask_"):
                target = name.replace("ask_", "")
                print(f"\n\n[📢 Delegation] {event.agent_name} -> {target}...")
            else:
                print(f"\n[🛠️ Tool] {event.agent_name} uses {name}")

    print("\n\n" + "-" * 40)
    print("✅ Mission Complete")

if __name__ == "__main__":
    main()
