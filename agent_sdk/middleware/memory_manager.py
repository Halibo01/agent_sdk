import json
from agent_sdk.agent import Agent
from agent_sdk.client import OpenRouterClient

def summarize_memory(agent: Agent, client: OpenRouterClient, threshold: int = 15, keep_last: int = 5):
    """
    Ajanın hafızasını kontrol eder ve belirli bir sınırı aşarsa eski mesajları özetler.
    
    Args:
        agent: Hafızası kontrol edilecek ajan.
        client: Özetleme işlemini yapacak LLM istemcisi.
        threshold: Hafıza bu sayıdan fazlaysa özetleme tetiklenir.
        keep_last: Son kaç mesajın özetlenmeden korunacağı (sıcak bağlam).
    """
    
    # 1. Kontrol: Hafıza sınırı aşıldı mı?
    if len(agent.memory) <= threshold:
        return

    print(f"\n[MemoryManager] {agent.name} hafızası şişti ({len(agent.memory)} mesaj). Özetleniyor...")

    # 2. Hafızayı Bölümle
    # [0] -> System Prompt (Koru)
    # [1 : -keep_last] -> Özetlenecek Kısım (Eskiler)
    # [-keep_last :] -> Sıcak Bağlam (Koru)
    
    system_prompt = agent.memory[0]
    to_summarize = agent.memory[1 : -keep_last]
    recent_context = agent.memory[-keep_last:]

    # Eğer özetlenecek bir şey yoksa çık
    if not to_summarize:
        return

    # 3. Özetleme İstemi Oluştur
    # Mesajları okunabilir metne çevir
    conversation_text = ""
    for msg in to_summarize:
        role = msg.get("role", "unknown")
        content = msg.get("content") or ""
        # Tool call detaylarını atlayıp sadece sonuçları alabiliriz veya hepsini verebiliriz.
        # Basitlik için content'i alıyoruz.
        conversation_text += f"{role.upper()}: {content}\n"

    summarizer_prompt = [
        {"role": "system", "content": "You are a helpful assistant that summarizes conversation histories."},
        {"role": "user", "content": f"Summarize the following conversation history into a concise paragraph. Preserve key facts, decisions, and outcomes.\n\nCONVERSATION:\n{conversation_text}"}
    ]

    # 4. LLM Çağrısı (Özetleme)
    try:
        # Client'ın chat (non-stream) metodunu kullanıyoruz
        response = client.chat(
            model="mistralai/devstral-2512:free", # Hızlı ve ucuz bir model seçilebilir
            messages=summarizer_prompt
        )
        summary_text = response["content"]
        
        # 5. Hafızayı Güncelle
        new_memory = [
            system_prompt, # Orijinal System Prompt
            {"role": "system", "content": f"[Previous Conversation Summary]: {summary_text}"},
        ] + recent_context # Son mesajlar
        
        agent.memory = new_memory
        print(f"[MemoryManager] Hafıza sıkıştırıldı. Yeni boyut: {len(agent.memory)}")

    except Exception as e:
        print(f"[MemoryManager] Hata oluştu: {e}")
