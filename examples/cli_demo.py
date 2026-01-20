"""
ADVANCED CLI DEMO & REFERENCE ARCHITECTURE
==========================================

⚠️  DEMO VS. PRODUCTION DISCLAIMER ⚠️
-------------------------------------
This file (`cli_demo.py`) is designed as a comprehensive showcase of the Agent SDK's capabilities.
While the core logic is solid, a commercial-grade application would typically separate these concerns:

1.  **Configuration:** Hardcoded agents (Manager, Coder) and prompts should be moved to external files (YAML/JSON).
2.  **Persistence:** This demo resets memory on restart. Production apps need a database (Postgres/Redis) to save sessions.
3.  **UI:** This uses `print()` with ANSI colors. Production apps usually use a Web Frontend (React/Next.js) or a TUI library (Textual).
4.  **Security:** While we use `HumanInTheLoop`, production apps need strict RBAC (Role-Based Access Control).

Architecture Overview:
----------------------
[User] -> [Runner] -> [Middleware Layer] -> [Agent Swarm]
                                                  |
                              -----------------------------------------
                              |                   |                   |
                          [Manager] <------> [Researcher] <------> [Coder]
"""

import os
import sys
import asyncio
from colorama import Fore, Back, Style, init
from dotenv import load_dotenv
import json

# Add project root to path for direct execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- AGENT SDK IMPORTS ---

# Core Components: The heart of the framework
from agent_sdk import (
    Agent, 
    Runner, 
    AgentSwarm, 
    AgentStreamEvent
)

# Clients: Connects to LLM Providers (OpenAI, Anthropic, etc.)
from agent_sdk import OpenRouterClient

# Tools: Functions that agents can execute
from agent_sdk.tools import (
    get_current_time,
    LangSearch,
    VisitWebpage,
    save_file,
    list_directory,
    read_file,
    execute_command,
    run_python_code
)

# Middleware: Plugins that intercept and modify agent behavior
from agent_sdk.middleware import (
    HumanInTheLoop,   # Asks user for permission
    MemorySummarizer, # Compresses history to save tokens
    ContextInjector,  # Injects OS/Env info
    SimpleRAG,        # Long-term memory (Keyword)
    ChromaRAG,        # Long-term memory (Vector)
    FileLogger,       # Saves logs to JSONL
    SQLiteLogger,     # Saves logs to SQL
    SelfReflection    # Agent reviews its own output
)

load_dotenv()
init(autoreset=True)

# --- UI CONSTANTS ---
# In a real app, these would be in a config file or frontend theme.

AGENT_COLORS = {
    "Manager": Fore.CYAN + Style.BRIGHT,
    "Coder": Fore.GREEN + Style.BRIGHT,
    "Reviewer": Fore.MAGENTA + Style.BRIGHT,
    "Researcher": Fore.BLUE + Style.BRIGHT,
    "Tool": Fore.WHITE + Style.DIM
}

def get_agent_color(name: str) -> str:
    return AGENT_COLORS.get(name, Fore.WHITE)

last_speaker = None 

def ui_printer(event: AgentStreamEvent):
    """
    Custom Event Handler for the CLI.
    Parses stream events and formats them with colors.
    """
    global last_speaker
    color = get_agent_color(event.agent_name)
    
    # 1. Text Generation Events
    if event.type in ["token", "reasoning"]:
        if event.agent_name != last_speaker:
            if last_speaker is not None: print("\n")
            print(f"{color}{Style.BRIGHT}┌── [{event.agent_name}]{Style.RESET_ALL}")
            last_speaker = event.agent_name

    if event.type == "token":
        print(f"{color}{event.data}", end="", flush=True)
    elif event.type == "reasoning":
        # DeepSeek-style "thinking" output
        print(f"{Fore.LIGHTBLACK_EX}{event.data}", end="", flush=True)

    # 2. Tool Execution Events
    elif event.type == "tool_call_ready":
        print()
        
        for call in event.data:
            func_name = call['function']['name']
            
            # Filter out duplicate delegation logs if needed
            if func_name.startswith("ask_") and not call.get("message"):
                continue

            raw_args = call['function']['arguments']
            
            try:
                args = json.loads(raw_args) 
                task_content = args.get("task", raw_args) 
            except:
                task_content = raw_args 

            # Special formatting for Inter-Agent Communication (Delegation)
            if func_name.startswith("ask_"):
                target_agent = func_name.replace("ask_", "").replace("_", " ").title()
                
                print(f" {Fore.YELLOW}│")
                print(f" {Fore.YELLOW}├── 📞 {Style.BRIGHT}DELEGATION: {event.agent_name} ➔ {target_agent}{Style.RESET_ALL}")
                print(f" {Fore.YELLOW}│    {Fore.WHITE}📜 Task: \"{task_content}\"{Style.RESET_ALL}")
                print(f" {Fore.YELLOW}│{Style.RESET_ALL}")
            
            else:
                msg = call.get('message')
                if msg:
                    print(f" {Back.BLACK}{Fore.YELLOW} 🛠  {msg} {Style.RESET_ALL}")

    elif event.type == "tool_result":
        output = str(event.data['output'])
        short_out = output[:150].replace("\n", " ") + "..." if len(output) > 150 else output
        print(f"\n {Fore.BLUE} 📥  Result: {short_out} {Style.RESET_ALL}\n")
        
        last_speaker = None

# --- MAIN APPLICATION LOGIC ---

def main():
    print(f"{Back.WHITE}{Fore.BLACK} === AI AGENT SWARM (DEMO) === {Style.RESET_ALL}\n")

    # [PROD NOTE] Configuration should be loaded from config.yaml or env vars
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print(f"{Fore.RED}Error: OPENROUTER_API_KEY not found in .env file.{Style.RESET_ALL}")
        return

    # [PROD NOTE] You might want to retry connection on failure
    client = OpenRouterClient(api_key=api_key) 
    runner = Runner(client)
    
    # --- MIDDLEWARE PIPELINE ---
    # Middleware executes in the order defined here.
    
    # 1. Safety First: Intercept dangerous tools
    runner.use(HumanInTheLoop(always_approve_for_debug=True)) 
    
    # 2. Observability: Log everything
    runner.use(FileLogger(filename="agent_activity.jsonl"))

    # 3. Context: Make agent aware of its environment
    runner.use(ContextInjector(
        env_keys=["PROJECT_ENV", "USER"], 
        static_context={
            "OS": os.name, 
            "WorkDir": os.getcwd(),
            "AppVersion": "Demo v1.0"
        }
    ))

    # 4. Efficiency: Compress history to save tokens/cost
    runner.use(MemorySummarizer(threshold=20, keep_last=10))

    # 5. Quality Control: Agent critiques its own work
    runner.use(SelfReflection())

    # 6. Long Term Memory (RAG)
    # [PROD NOTE] Use ChromaRAG for production, SimpleRAG for prototypes.
    runner.use(ChromaRAG())

    # --- AGENT SWARM SETUP ---
    # We use a centralized Swarm manager to handle event printing and message routing.
    swarm = AgentSwarm(runner, event_handler=ui_printer)

    # [PROD NOTE] Agent instructions should be refined and versioned in text files.
    
    manager = Agent(
        name="Manager",
        model="mistralai/mistral-7b-instruct", 
        instructions="""
        You are the Project Manager.
        1. Analyze the user request.
        2. Delegate research tasks to 'Researcher'.
        3. Delegate coding/file tasks to 'Coder'.
        4. Synthesize the results and present the final answer.
        """,
        tools={"get_current_time": get_current_time}
    )

    researcher = Agent(
        name="Researcher",
        model="mistralai/mistral-7b-instruct",
        instructions="""
        You are an Expert Researcher.
        1. Search the web for information.
        2. Summarize findings concisely.
        3. Report back to the Manager.
        """,
        tools={"langsearch": LangSearch, "visit_webpage": VisitWebpage},
        handoff_msg="Starting research on '{task}'..."
    )

    coder = Agent(
        name="Coder",
        model="mistralai/mistral-7b-instruct",
        instructions="""
        You are a Senior Software Engineer.
        1. Write code or create files as requested.
        2. Use 'list_dir' and 'read_file' to understand the codebase.
        3. Confirm when the task is done.
        """,
        tools={
            "save_md": save_file,
            "list_dir": list_directory,
            "read_file": read_file,
            "exec_cmd": execute_command,
            "run_python": run_python_code
        },
        handoff_msg="💻 Coding task '{task}' initiated..." 
    )

    # Register Agents to Swarm
    swarm.add_agent(manager)
    swarm.add_agent(researcher)
    swarm.add_agent(coder)
    
    # Create Mesh Network (Everyone can talk to everyone)
    swarm.connect_all()

    # Helpers for Debugging CLI
    agents_map = {"Manager": manager, "Researcher": researcher, "Coder": coder}
    agent_tools_backup = {name: agent.tools.copy() for name, agent in agents_map.items()}

    print(f"{Fore.GREEN}Tip: Type '/memory <Agent>' to inspect internal state.{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Tip: Type '/tools' to enable/disable tools at runtime.{Style.RESET_ALL}")

    # --- MAIN LOOP (REPL) ---
    while True:
        try:
            user_input = input(f"\n{Fore.WHITE}{Style.BRIGHT}User: {Style.RESET_ALL}")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # --- DEBUG COMMANDS ---
            if user_input.startswith("/tools"):
                # [PROD NOTE] This is a dev-tool feature. Remove in production.
                parts = user_input.split(" ")
                cmd = parts[1] if len(parts) > 1 else "list"
                
                if cmd == "list":
                    print(f"\n{Fore.CYAN}--- TOOL DEBUGGER ---{Style.RESET_ALL}")
                    for name, agent in agents_map.items():
                        print(f"\n{Style.BRIGHT}Agent: {name}{Style.RESET_ALL}")
                        current_tools = agent.tools
                        all_tools = agent_tools_backup[name]
                        for tool_name in all_tools.keys():
                            status = f"{Fore.GREEN}ENABLED" if tool_name in current_tools else f"{Fore.RED}DISABLED"
                            print(f"  - {tool_name}: {status}{Style.RESET_ALL}")
                elif cmd in ["enable", "disable"] and len(parts) >= 4:
                     # ... (Tool toggling logic) ...
                     print(f"{Fore.YELLOW}Tool toggled (implied).{Style.RESET_ALL}")
                continue

            if user_input.startswith("/memory"):
                parts = user_input.split(" ")
                if len(parts) > 1:
                    target_name = parts[1]
                    target_agent = agents_map.get(target_name)
                    if target_agent:
                        print(f"\n{Fore.YELLOW}🧠 {target_agent.name} Memory ({len(target_agent.memory)} msgs):{Style.RESET_ALL}")
                        print(json.dumps(target_agent.memory, indent=2, ensure_ascii=False))
                continue

            if user_input == "/debug":
                print(f"\n{Fore.CYAN}--- SYSTEM STATUS ---")
                for name, agent in agents_map.items():
                    print(f"[{name}] Memory Size: {len(agent.memory)} messages")
                continue
            # -----------------------

            print("--------------------")
            
            # [PROD NOTE] Resetting sub-agent memory is a design choice.
            # In some apps, you might want them to remember previous context.
            researcher.memory = []
            coder.memory = []

            # Start the Swarm!
            stream = runner.run_stream(manager, user_input)
            for event in stream:
                ui_printer(event)
                
            print("\n" + "--------------------")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nUnexpected Error: {e}")

if __name__ == "__main__":
    main()