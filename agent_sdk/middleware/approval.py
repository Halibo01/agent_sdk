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
            approval_callback: (agent_name, tool_name, args, tool_call_id) -> "approve" | "reject" | "allow_always"
            always_approve_for_debug: If True, bypasses all checks.
        """
        self.always_approve_for_debug = always_approve_for_debug
        self.session_approved_tools = {}
        self.approval_callback = approval_callback or self._default_console_callback

    def _default_console_callback(self, agent_name: str, tool_name: str, args: dict, tool_call_id: str = None) -> str:
        """Default console-based approval mechanism."""
        print(f"\n{Fore.RED}{Style.BRIGHT}🛑 HUMAN APPROVAL REQUIRED 🛑{Style.RESET_ALL}")
        print(f"Agent '{agent_name}' wants to execute the following action:")
        
        # Show arguments nicely
        print(f"{Fore.CYAN}Tool: {tool_name}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Args: {json.dumps(args, indent=2)}{Style.RESET_ALL}")
        
        print(f"{Fore.WHITE}Options:{Style.RESET_ALL}")
        print(f"  [y]es    : Approve this action")
        print(f"  [n]o     : Deny this action")
        print(f"  [a]lways : Approve '{tool_name}' for this session")
        
        response = input(f"{Fore.WHITE}Choice? (y/n/a): {Style.RESET_ALL}").lower().strip()
        
        if response in ['y', 'yes', 'evet']:
            return "approve"
        elif response in ['a', 'always', 'session', 'surekli']:
            return "allow_always"
        elif response in ['n', 'no', 'hayir']:
            return "reject"
        
        return "reject"

    def before_tool_execution(self, agent, runner, tool_name: str, tool_args: dict, tool_call_id: str = None) -> bool:
        """Sync onay mekanizması"""
        if self.always_approve_for_debug: return True
        args_key = json.dumps(tool_args, sort_keys=True)
        if tool_name in self.session_approved_tools and args_key in self.session_approved_tools[tool_name]: return True

        tool_func = agent.tools.get(tool_name)
        if not tool_func: return True
        requires_approval = getattr(tool_func, "_approval_required", False)
        if not requires_approval: return True

        # Callback çağır (Sync varsayımıyla, çünkü metod sync)
        if asyncio.iscoroutinefunction(self.approval_callback):
            print(f"{Fore.RED}Error: Async callback cannot be used in Sync mode.{Style.RESET_ALL}")
            return False

        decision = self.approval_callback(agent.name, tool_name, tool_args, tool_call_id)
        return self._process_decision(decision, tool_name, tool_args)

    async def before_tool_execution_async(self, agent, runner, tool_name: str, tool_args: dict, tool_call_id: str = None) -> bool:
        """Async onay mekanizması"""
        if self.always_approve_for_debug: return True
        args_key = json.dumps(tool_args, sort_keys=True)
        if tool_name in self.session_approved_tools and args_key in self.session_approved_tools[tool_name]: return True

        tool_func = agent.tools.get(tool_name)
        if not tool_func: return True
        requires_approval = getattr(tool_func, "_approval_required", False)
        if not requires_approval: return True

        # Callback çağır
        if inspect.iscoroutinefunction(self.approval_callback):
            decision = await self.approval_callback(agent.name, tool_name, tool_args, tool_call_id)
        else:
            if self.approval_callback == self._default_console_callback:
                decision = await asyncio.to_thread(self._default_console_callback, agent.name, tool_name, tool_args, tool_call_id)
            else:
                decision = self.approval_callback(agent.name, tool_name, tool_args, tool_call_id)

        return self._process_decision(decision, tool_name, tool_args)

    def _process_decision(self, decision: str, tool_name: str, tool_args: dict) -> bool:
        if decision == "approve":
            print(f"{Fore.GREEN}✓ Action Approved.{Style.RESET_ALL}")
            return True
        elif decision == "allow_always":
            args_key = json.dumps(tool_args, sort_keys=True)
            self.session_approved_tools.setdefault(tool_name, set()).add(args_key)
            print(f"{Fore.GREEN}✓ '{tool_name}' approved for this session.{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}X Action Rejected.{Style.RESET_ALL}")
            return False