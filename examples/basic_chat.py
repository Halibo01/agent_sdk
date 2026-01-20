"""
Basic Chat Example
------------------
This script demonstrates the simplest usage of the Agent SDK:
1. Connecting to an LLM Provider (OpenRouter/OpenAI).
2. Creating a Runner.
3. Streaming a response to the console.

Usage:
    python examples/basic_chat.py
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to sys.path to ensure agent_sdk is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_sdk import Runner, Agent, OpenRouterClient

# Load environment variables
load_dotenv()

def main():
    # 1. Configuration
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: API Key not found. Please set OPENROUTER_API_KEY in .env")
        return

    # 2. Initialize Client
    try:
        # You can swap this with OpenAIClient, GeminiClient, etc.
        client = OpenRouterClient(api_key=api_key)
    except Exception as e:
        print(f"❌ Error initializing client: {e}")
        return

    # 3. Initialize Runner
    runner = Runner(client)

    # 4. Define Agent
    assistant = Agent(
        name="Assistant",
        model="mistralai/mistral-7b-instruct", # Change model as needed
        instructions="You are a helpful, concise AI assistant."
    )

    print(f"🤖 Agent '{assistant.name}' is ready. Type 'exit' to quit.\n")

    # 5. Chat Loop
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                print("👋 Goodbye!")
                break
            
            if not user_input.strip():
                continue

            print("Agent: ", end="", flush=True)

            # 6. Run & Stream
            # The runner handles history automatically for the active session
            stream = runner.run_stream(assistant, user_input)
            
            for event in stream:
                if event.type == "token":
                    print(event.data, end="", flush=True)
                elif event.type == "error":
                    print(f"\n❌ Error: {event.data}")
            
            print("\n")

        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
