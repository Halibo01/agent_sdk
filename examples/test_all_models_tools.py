import os
import glob
from agent_sdk.clients.llamacpp import LlamaCppClient
from agent_sdk import Agent, Runner
from colorama import Fore, Style, init

init(autoreset=True)

def get_weather(location: str) -> str:
    """Gets the current weather for a specific location."""
    return f"The weather in {location} is 22C."

def main():
    models_dir = r"C:\Users\Asus\Downloads\models"
    
    if not os.path.exists(models_dir):
        print(f"Directory not found: {models_dir}")
        return
        
    gguf_files = glob.glob(os.path.join(models_dir, "*.gguf"))
    
    if not gguf_files:
        print("No .gguf files found in the directory.")
        return
        
    print(f"{Fore.CYAN}--- MODEL TOOL ÇAĞIRMA (RE-ACT) TESTİ ---{Style.RESET_ALL}")
    print(f"Toplam {len(gguf_files)} model bulundu. Sırayla test ediliyor...\n")
    
    for model_path in gguf_files:
        model_name = os.path.basename(model_path)
        print(f"\n{Fore.YELLOW}===================================================={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}TEST EDİLEN MODEL: {model_name}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}===================================================={Style.RESET_ALL}")
        
        try:
            client = LlamaCppClient(model_path=model_path, n_ctx=2048, n_gpu_layers=-1, preload_all=False)
            
            agent = Agent(
                name="TesterAgent",
                model="local",
                tools={"get_weather": get_weather},
                instructions="You are a helpful assistant. You MUST use the 'get_weather' tool to find out the weather in Tokyo. Do not invent the weather.",
                generation_config={"max_tokens": 150} # Keep it short for testing
            )
            
            runner = Runner(client)
            
            print(f"{Fore.MAGENTA}Soru: 'What is the weather in Tokyo today?'{Style.RESET_ALL}\n")
            
            raw_output = ""
            tool_called = False
            
            events = runner.run_stream(agent, "What is the weather in Tokyo today?")
            
            for event in events:
                if event.type == "token":
                    raw_output += event.data
                    print(event.data, end="", flush=True)
                elif event.type == "tool_call_ready":
                    tool_called = True
                    print(f"\n\n{Fore.GREEN}[BAŞARILI] -> Sistem bu metni bir Tool Call olarak başarıyla ayrıştırdı!{Style.RESET_ALL}")
                    print(f"Çekilen Veri: {event.data}")
                    break # Stop reading after first tool call to save time
                    
            if not tool_called:
                print(f"\n\n{Fore.RED}[BAŞARISIZ] -> Model aracı çağıramadı veya desteklenmeyen bir metin üretti.{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"\n{Fore.RED}Model test edilirken hata oluştu: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
