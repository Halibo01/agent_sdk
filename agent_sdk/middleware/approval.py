from .base import Middleware
from colorama import Fore, Style
import json
from typing import Callable, Optional
import inspect
import asyncio

class HumanInTheLoop(Middleware):
    def __init__(self, approval_callback: Optional[Callable] = None, always_approve_for_debug: bool = False):
        """
        Args:
            approval_callback: (agent_name, tool_name, args, tool_call_id) -> "approve" | "reject" | "always"
            always_approve_for_debug: If True, bypasses all checks.
        """
        self.always_approve_for_debug = always_approve_for_debug
        self.session_approved_tools = set()
        self.approval_callback = approval_callback or self._default_console_callback

    def _default_console_callback(self, agent_name: str, tool_name: str, args: dict, tool_call_id: str = None) -> str:
        """
        Varsayılan konsol tabanlı onay mekanizması.
        """
        print(f"\n{Fore.RED}{Style.BRIGHT}🛑 İNSAN ONAYI GEREKİYOR 🛑{Style.RESET_ALL}")
        print(f"Agent '{agent_name}' şu işlemi yapmak istiyor:")
        print(f"Tool: {Fore.YELLOW}{tool_name}{Style.RESET_ALL}")
        if tool_call_id:
            print(f"Call ID: {tool_call_id}")
        print(f"Args: {json.dumps(args, indent=2, ensure_ascii=False)}")
        
        while True:
            print(f"{Fore.WHITE}Seçenekler:{Style.RESET_ALL}")
            print(f"  [y]es    : Bu seferlik onayla")
            print(f"  [n]o     : Reddet")
            print(f"  [a]lways : Bu oturum boyunca '{tool_name}' için onayla")
            
            response = input(f"{Fore.WHITE}Seçiminiz? (y/n/a): {Style.RESET_ALL}").lower().strip()
            
            if response in ['y', 'yes', 'evet']:
                return "approve"
            elif response in ['a', 'always', 'session', 'sürekli']:
                return "always"
            elif response in ['n', 'no', 'hayır']:
                return "reject"

    def before_tool_execution(self, agent, runner, tool_name: str, tool_args: dict, tool_call_id: str = None) -> bool:
        """Sync onay mekanizması"""
        if self.always_approve_for_debug: return True
        if tool_name in self.session_approved_tools: return True

        tool_func = agent.tools.get(tool_name)
        if not tool_func: return True
        requires_approval = getattr(tool_func, "_approval_required", False)
        if not requires_approval: return True

        # Callback çağır (Sync varsayımıyla, çünkü metod sync)
        if inspect.iscoroutinefunction(self.approval_callback):
             # Sync metod içinde async callback çalıştıramayız (kolayca), hata fırlatabiliriz veya loop açmalıyız.
             # Basitlik için burada sync bekliyoruz.
             print(f"{Fore.RED}Hata: Sync çalışma modunda Async callback kullanılamaz.{Style.RESET_ALL}")
             return False
        
        # Güncellenmiş imza: tool_call_id eklendi
        decision = self.approval_callback(agent.name, tool_name, tool_args, tool_call_id)
        return self._process_decision(decision, tool_name)

    async def before_tool_execution_async(self, agent, runner, tool_name: str, tool_args: dict, tool_call_id: str = None) -> bool:
        """Async onay mekanizması"""
        if self.always_approve_for_debug: return True
        if tool_name in self.session_approved_tools: return True

        tool_func = agent.tools.get(tool_name)
        if not tool_func: return True
        requires_approval = getattr(tool_func, "_approval_required", False)
        if not requires_approval: return True

        # Callback çağır
        if inspect.iscoroutinefunction(self.approval_callback):
            decision = await self.approval_callback(agent.name, tool_name, tool_args, tool_call_id)
        else:
            # Eğer default callback (konsol) ise ve bloklayıcıysa thread'e at
            if self.approval_callback == self._default_console_callback:
                decision = await asyncio.to_thread(self._default_console_callback, agent.name, tool_name, tool_args, tool_call_id)
            else:
                # Kullanıcı custom sync callback verdiyse direkt çağır (riski kullanıcıya ait)
                decision = self.approval_callback(agent.name, tool_name, tool_args, tool_call_id)

        return self._process_decision(decision, tool_name)

    def _process_decision(self, decision: str, tool_name: str) -> bool:
        """Ortak karar işleme mantığı"""
        if decision == "approve":
            print(f"{Fore.GREEN}✓ İşlem Onaylandı.{Style.RESET_ALL}")
            return True
        elif decision == "always":
            self.session_approved_tools.add(tool_name)
            print(f"{Fore.GREEN}✓ '{tool_name}' bu oturum için onaylandı.{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}X İşlem Reddedildi.{Style.RESET_ALL}")
            return False
