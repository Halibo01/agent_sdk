from .base import Middleware
import os
from typing import List, Dict, Optional

class ContextInjector(Middleware):
    def __init__(self, env_keys: Optional[List[str]] = None, static_context: Optional[Dict[str, str]] = None):
        """
        Args:
            env_keys: .env veya sistemden okunacak ortam değişkenlerinin isimleri. (Örn: ['APP_ENV', 'PROJECT_ROOT'])
            static_context: Sabit olarak eklemek istediğiniz anahtar-değer çiftleri. (Örn: {'User': 'Admin', 'OS': 'Windows'})
        """
        self.env_keys = env_keys or []
        self.static_context = static_context or {}

    def before_run(self, agent, runner):
        """
        Agent çalışmadan hemen önce hafızasına bağlam verilerini enjekte eder.
        """
        context_lines = []

        # 1. Environment Variable'ları Oku
        if self.env_keys:
            found_envs = False
            for key in self.env_keys:
                val = os.getenv(key)
                if val:
                    if not found_envs:
                        context_lines.append("--- Environment Context ---")
                        found_envs = True
                    context_lines.append(f"{key}: {val}")

        # 2. Statik Verileri Ekle
        if self.static_context:
            context_lines.append("--- Runtime Context ---")
            for k, v in self.static_context.items():
                context_lines.append(f"{k}: {v}")

        # Eğer eklenecek bir şey yoksa çık
        if not context_lines:
            return

        # Mesajı oluştur
        injection_content = "\n".join(context_lines)
        system_note = f"\n[SYSTEM NOTICE: The following context is active for this session]\n{injection_content}\n"

        # 3. Tekrarı Önleme (Gelişmiş Kontrol)
        # Hafızada bu system_note zaten varsa tekrar ekleme.
        for msg in agent.memory:
            if msg.get("role") == "system" and injection_content in msg.get("content", ""):
                return

        # Hafızaya ekle
        # System rolü ile ekliyoruz ki ajan bunu bir talimat değil, bilgi olarak görsün.
        agent.memory.append({
            "role": "system",
            "content": system_note
        })

        print(f"[ContextInjector] {agent.name} için bağlam yüklendi.")
