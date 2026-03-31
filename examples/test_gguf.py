import os
from agent_sdk.clients.llamacpp import LlamaCppClient
from agent_sdk.grammar import GrammarBuilder
from agent_sdk import Agent, Runner

def main():
    # 1. Path to your specific model
    model_path = r"..\..\..\My project (1)\Assets\Scripts\qwen2.5-coder-1.5b-instruct-q3_k_m.gguf"
    
    if not os.path.exists(model_path):
        print(f"Hata: Model bulunamadı: {os.path.abspath(model_path)}")
        return

    print(f"Model yükleniyor: {model_path}")
    print("Lütfen bekleyin, bu işlem modelin boyutuna göre biraz sürebilir...\n")
    
    # 2. Initialize the GGUF Client
    # n_gpu_layers=-1 attempts to offload everything to GPU if CUDA is available.
    # Set to 0 if you want to use CPU only.
    client = LlamaCppClient(model_path=model_path, n_ctx=0, n_gpu_layers=-1)
    
    # 3. Build a Strict Grammar using GrammarBuilder
    builder = GrammarBuilder()
    schema = dict(
        assistant_profile=dict(
            ai_name=str,
            primary_language=str,
            is_ready=bool,
            lines_of_code_analyzed=int
        )
    )
    json_grammar = builder.to_json(**schema)
    
    # 4. Create the Agent with the Grammar
    agent = Agent(
        name="QwenCoder",
        model="local", # Model name is ignored for llama.cpp as it's defined by the path
        instructions="You are a brilliant AI programming assistant. Introduce yourself strictly in JSON.",
        output_schema=json_grammar,
        output_format="json"
    )
    
    runner = Runner(client)
    
    print("--- AJAN ÇALIŞIYOR (STRICT JSON GRAMMAR İLE) ---")
    
    # 5. Run the streaming chat
    events = runner.run_stream(agent, "Hi! Tell me about yourself.")
    
    for event in events:
        if event.type == "token":
            print(event.data, end="", flush=True)
            
    print("\n\n--- TEST BAŞARIYLA TAMAMLANDI ---")
    
    # Print token usage
    print("\nMaliyet ve Token Kullanımı:")
    print(client.get_cost_summary())

if __name__ == "__main__":
    main()
