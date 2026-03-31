import os
from agent_sdk.clients.llamacpp import LlamaCppClient
from agent_sdk import Agent, Runner, AgentBridge
from colorama import Fore, Style, init

init(autoreset=True)

# --- YENİ BİR ARAÇ (CODER İÇİN) ---
def write_to_file(filename: str, content: str) -> str:
    """Writes the given content to a file on the disk."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"SUCCESS: File '{filename}' has been written to disk successfully."
    except Exception as e:
        return f"ERROR: Could not write to file. {str(e)}"

def main():
    print(f"{Fore.CYAN}--- ZİNCİRLEME MULTI-AGENT VRAM SWAP TESTİ ---{Style.RESET_ALL}\n")
    
    # 1. Modeller
    qwen_path = r"C:\Users\Asus\Downloads\models\Qwen3.5-4B-Q4_K_M.gguf"
    falcon_path = r"C:\Users\Asus\Downloads\models\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    
    for path in [qwen_path, falcon_path]:
        if not os.path.exists(path):
            print(f"{Fore.RED}Error: Model bulunamadı: {path}{Style.RESET_ALL}")
            return

    # 2. İstemciler (preload_all=False ile Akıllı VRAM yönetimi aktif)
    client_coder = LlamaCppClient(model_path=qwen_path, n_ctx=2048, n_gpu_layers=-1)
    client_manager = LlamaCppClient(model_path=falcon_path, n_ctx=2048, n_gpu_layers=-1)
    
    runner_coder = Runner(client_coder)
    runner_manager = Runner(client_manager)
    
    # 3. CODER AJANI (Dosya yazma yetkisi var)
    agent_coder = Agent(
        name="Qwen_Coder",
        model="local",
        tools={"write_to_file": write_to_file}, # Fiziksel dünyaya etki edebilir
        instructions="""You are a Python Programmer. 
Your ONLY job is to write the code the user asks for AND save it to the disk using your 'write_to_file' tool.
Do not explain the code. Just use the tool to save it!""",
        generation_config={
            "stop": ["<|im_end|>", "</s>", "User:"],
            "frequency_penalty": 0.8,
            "max_tokens": 300
        }
    )
    
    # 4. MANAGER AJANI (Hiçbir yetkisi yok, Coder'a emir vermek zorunda)
    agent_manager = Agent(
        name="Falcon_Manager",
        model="local",
        instructions="""You are a strict Project Manager. 
You CANNOT write code and you CANNOT save files.
You MUST use your 'ask_coder' tool to instruct the coder to do the task.
Task: Tell the coder to create a python file that prints "Hello AI World".
Once you call the tool and get the success message, tell the user the job is done and STOP.""",
        generation_config={
            "stop": ["<|im_end|>", "</s>", "\nUser:", "Question:"],
            "frequency_penalty": 0.8,
            "presence_penalty": 0.5,
            "max_tokens": 150
        }
    )
    
    # 5. Köprü Kurulumu (Manager, Coder'ı bir 'araç' olarak kullanacak)
    bridge = AgentBridge(agent_coder, runner_coder)
    agent_manager.tools["ask_coder"] = bridge.create_tool()
    
    print(f"\n{Fore.GREEN}--- SİMÜLASYON BAŞLIYOR ---{Style.RESET_ALL}")
    
    events = runner_manager.run_stream(agent_manager, "Manager, please get the python script written and saved to disk.")
    
    for event in events:
        if event.type == "token":
            color = Fore.BLUE if event.agent_name == "Falcon_Manager" else Fore.MAGENTA
            print(f"{color}{event.data}{Style.RESET_ALL}", end="", flush=True)
        elif event.type == "tool_call_ready":
            print(f"\n\n{Fore.YELLOW}>>> [SİSTEM] {event.agent_name} ARAÇ ÇAĞIRIYOR: {event.data[0]['function']['name']}{Style.RESET_ALL}\n")
        elif event.type == "tool_result":
            print(f"\n{Fore.CYAN}>>> [SİSTEM] Araç Sonucu: {str(event.data.get('output', ''))[:100]}...{Style.RESET_ALL}\n")

    print(f"\n\n{Fore.GREEN}--- TEST BAŞARIYLA TAMAMLANDI ---{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
