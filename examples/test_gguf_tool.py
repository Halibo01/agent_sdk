import os
from agent_sdk.clients.llamacpp import LlamaCppClient
from agent_sdk import Agent, Runner

def get_weather(location: str) -> str:
    """Gets the current weather for a specific location."""
    print(f"\n[TOOL EXECUTION] get_weather called with location='{location}'")
    return f"The weather in {location} is currently 22 degrees Celsius."

def main():
    model_path = r"C:\Users\Asus\Downloads\Qwen3.5-4B-Q4_K_M.gguf"
    
    if not os.path.exists(model_path):
        print(f"Hata: Model bulunamadı: {os.path.abspath(model_path)}")
        return

    print(f"Model yükleniyor: {model_path}\n")
    client = LlamaCppClient(model_path=model_path, n_ctx=2048, n_gpu_layers=-1)
    
    agent = Agent(
        name="LocalWeatherBot",
        model="local",
        tools={"get_weather": get_weather},
        instructions="You are a helpful assistant. Use the tools provided to you if necessary."
    )
    
    runner = Runner(client)
    
    print("--- AJAN ÇALIŞIYOR ---")
    events = runner.run_stream(agent, "What is the weather in Tokyo today?")
    
    for event in events:
        if event.type == "token":
            print(event.data, end="", flush=True)
        elif event.type == "tool_call_ready":
            print(f"\n[Ajan] Tool çağırma kararı aldı: {event.data}")
        elif event.type == "tool_result":
            print(f"\n[Ajan] Tool sonucu aldı: {event.data['output']}")
            print("[Ajan] Final cevabı üretiyor...\n")
            
    print("\n--- TEST BAŞARIYLA TAMAMLANDI ---")

if __name__ == "__main__":
    main()
