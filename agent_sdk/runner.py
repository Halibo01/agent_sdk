import json
import inspect
import asyncio
from typing import List, Dict, Any, Generator, AsyncGenerator, get_type_hints, Optional
from .agent import Agent
from .events import AgentStreamEvent

# 1. TİP HARİTASI (Python -> JSON Schema)
PYTHON_TO_JSON = {
    int: "integer",
    float: "number",
    str: "string",
    bool: "boolean",
    list: "array",
    dict: "object"
}

# 2. ÖZEL MODELLER (Reasoning/Thinking)
# Bu modeller Tool kullanamaz ve System Prompt sevmezler.
REASONING_KEYWORDS = [
    "o1-", "o1-mini", "o1-preview", 
    "r1", "reasoner", "think", 
    "chimera", "deepseek-r1"
]

class Runner:
    def __init__(self, client):
        self.client = client
        # Caller ID için Yığın (Stack) Yapısı
        # En altta her zaman "User" vardır.
        self.agent_stack = ["User"]
        self.middlewares = []

    def use(self, middleware):
        """Runner'a bir middleware ekler."""
        self.middlewares.append(middleware)

    @property
    def current_sender(self) -> str:
        """Şu an bu fonksiyonu çağıran (Aktif) ajanın ismini döner."""
        return self.agent_stack[-1] if self.agent_stack else "User"

    def _is_reasoning_model(self, model_name: str) -> bool:
        """Modelin tool destekleyip desteklemediğini kontrol eder."""
        return any(keyword in model_name.lower() for keyword in REASONING_KEYWORDS)

    def _prepare_messages(self, agent: Agent, input_text: str, history: List[Dict]) -> List[Dict]:
        """
        Reasoning modelleri için 'system' rolünü 'user'a çevirir.
        Normal modeller için standart yapı kurar.
        """
        messages = []
        is_reasoning = self._is_reasoning_model(agent.model)

        # 1. System Prompt
        if agent.instructions:
            if is_reasoning:
                messages.append({
                    "role": "user", 
                    "content": f"Instructions:\n{agent.system_prompt()}"
                })
            else:
                messages.append({
                    "role": "system", 
                    "content": agent.system_prompt()
                })

        # 2. Geçmişi Ekle
        if history:
            messages.extend(history)

        # 3. Yeni Girdi
        messages.append({"role": "user", "content": input_text})
        
        return messages

    def _tool_schema(self, agent: Agent) -> Optional[List[Dict]]:
        """
        Agent'ın fonksiyonlarını JSON şemasına çevirir.
        Eğer model reasoning ise Tool göndermez.
        """
        # A) Reasoning Modelleri Tool Kullanamaz
        if self._is_reasoning_model(agent.model):
            return None

        # B) Tool Yoksa None Dön
        if not agent.tools:
            return None

        schemas = []
        for name, fn in agent.tools.items():
            sig = inspect.signature(fn)
            hints = get_type_hints(fn)
            
            properties = {}
            required = []

            for param_name, param in sig.parameters.items():
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue
                
                py_type = hints.get(param_name, str)
                json_type = PYTHON_TO_JSON.get(py_type, "string")
                
                properties[param_name] = {"type": json_type}
                if param.default is inspect.Parameter.empty:
                    required.append(param_name)

            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": fn.__doc__ or "",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                }
            })
        return schemas

    def run(self, agent: Agent, task: str, chat_history: List[Dict] = None) -> str:
        """
        Runs the agent synchronously and returns the final response string.
        """
        final_output = ""
        stream = self.run_stream(agent, task, chat_history)
        for event in stream:
            if event.type == "token":
                final_output += str(event.data)
            elif event.type == "final":
                # 'final' event data might be a dict {"output": "..."} or just string
                data = event.data
                if isinstance(data, dict):
                    final_output = data.get("output", "")
                else:
                    final_output = str(data)
        return final_output

    async def run_async(self, agent: Agent, task: str, chat_history: List[Dict] = None) -> str:
        """
        Runs the agent asynchronously and returns the final response string.
        """
        final_output = ""
        stream = self.run_stream_async(agent, task, chat_history)
        async for event in stream:
            if event.type == "token":
                final_output += str(event.data)
            elif event.type == "final":
                data = event.data
                if isinstance(data, dict):
                    final_output = data.get("output", "")
                else:
                    final_output = str(data)
        return final_output

    def run_stream(self, agent: Agent, task: str, chat_history: List[Dict] = None) -> Generator[AgentStreamEvent, None, None]:
        """
        Ana Çalıştırma Döngüsü (Persistent Memory Destekli).
        """
        
        # 0. MIDDLEWARE: Before Run
        for mw in self.middlewares:
            mw.before_run(agent, self)

        # 1. CALLER ID: Bu agent'ı yığına ekle (Aktif çalışan yap)
        self.agent_stack.append(agent.name)

        # 2. HAFIZA BAŞLATMA (Eğer boşsa)
        if not agent.memory:
            # A) System Prompt Ekle
            if agent.instructions:
                is_reasoning = self._is_reasoning_model(agent.model)
                if is_reasoning:
                    # Reasoning modelleri system rolünü sevmez, user olarak ekle
                    agent.memory.append({
                        "role": "user", 
                        "content": f"Instructions:\n{agent.system_prompt()}"
                    })
                else:
                    agent.memory.append({
                        "role": "system", 
                        "content": agent.system_prompt()
                    })
            
            # B) Dışarıdan gelen history varsa ekle (İlk başlangıç için opsiyonel)
            if chat_history:
                agent.memory.extend(chat_history)

        # 3. YENİ GÖREVİ EKLE
        # Görevi her çağrıldığında hafızaya ekliyoruz.
        agent.memory.append({"role": "user", "content": task})

        try:
            # Sonsuz döngü koruması
            for step in range(agent.max_steps):
                
                # Tool Şemasını Hazırla
                tools = self._tool_schema(agent)

                # B) API İSTEĞİ (STREAM)
                try:
                    # ARTIK DOĞRUDAN HAFIZAYI KULLANIYORUZ
                    stream = self.client.chat_stream(
                        model=agent.model,
                        messages=agent.memory,
                        tools=tools,
                        **agent.generation_config
                    )
                except Exception as e:
                    error_msg = str(e)
                    if hasattr(e, 'response') and e.response is not None:
                        # API'den dönen detaylı hatayı ekle
                        error_msg += f"\nServer Response: {e.response.text}"
                    
                    print(f"\nAPI ERROR ({agent.name}): {error_msg}")
                    yield AgentStreamEvent("error", error_msg, agent.name)
                    return

                current_content = ""
                current_tool_calls = {}
                
                # --- STREAM LOOP ---
                for event in stream:
                    # Agent ismini işle (Runner sorumluluğu)
                    event.agent_name = agent.name
                    
                    yield event

                    # --- MIDDLEWARE STREAM HOOK ---
                    for mw in self.middlewares:
                        new_events = mw.process_stream_event(event, agent, self)
                        if new_events:
                            for ne in new_events:
                                ne.agent_name = agent.name
                                yield ne
                    # ------------------------------
                    
                    if event.type == "token":
                        current_content += str(event.data)
                        # yield event (Moved up)
                    
                    elif event.type == "reasoning":
                        # yield event (Moved up)
                        pass
                    
                    elif event.type == "tool_call":
                        # Tool call chunk birleştirme mantığı
                        tc_chunk = event.data
                        idx = tc_chunk.get("index", 0)
                        
                        if idx not in current_tool_calls:
                            current_tool_calls[idx] = {"id": tc_chunk.get("id"), "name": "", "arguments": ""}
                        
                        if "function" in tc_chunk:
                            fn = tc_chunk["function"]
                            if fn.get("name"): current_tool_calls[idx]["name"] = fn["name"]
                            if fn.get("arguments"): current_tool_calls[idx]["arguments"] += fn["arguments"]
                        
                        # UI Efekti için (Stream sırasında)
                        yield AgentStreamEvent("tool_call_ready", [tc_chunk], agent.name) # Type: tool_call_chunk diyebiliriz

                # --- KARAR ANI (LOOP SONU) ---
                
                # 1. Model cevabını HAFIZAYA EKLE
                assistant_msg = {"role": "assistant", "content": current_content if current_content else None}
                
                tool_calls_data = []
                if current_tool_calls:
                    for idx in sorted(current_tool_calls.keys()):
                        tc = current_tool_calls[idx]
                        tool_calls_data.append({
                            "id": tc.get("id") or f"call_{idx}_{step}",
                            "type": "function",
                            "function": {"name": tc["name"], "arguments": tc["arguments"]}
                        })
                    assistant_msg["tool_calls"] = tool_calls_data
                
                agent.memory.append(assistant_msg)

                # 2. Tool Çağrısı Yoksa -> BİTİR
                if not tool_calls_data:
                    yield AgentStreamEvent("final", {"output": current_content}, agent.name)
                    return

                # 3. Tool Varsa -> ÇALIŞTIR
                for tc in tool_calls_data:
                    call_id = tc["id"]
                    func_name = tc["function"]["name"]
                    raw_args = tc["function"]["arguments"]
                    
                    try:
                        args = json.loads(raw_args)
                    except:
                        args = {}

                    # --- MIDDLEWARE KONTROLÜ (Human-in-the-loop vb.) ---
                    should_run = True
                    for mw in self.middlewares:
                        # Eğer bir middleware False dönerse zinciri kır ve çalıştırma
                        # GÜNCELLEME: call_id eklendi
                        if not mw.before_tool_execution(agent, self, func_name, args, call_id):
                            should_run = False
                            break
                    
                    if not should_run:
                        msg = f"Tool '{func_name}' execution was blocked by a middleware."
                        print(f"\n{msg}")
                        
                        # Kullanıcıya bildir
                        yield AgentStreamEvent("tool_result", {
                            "name": func_name, 
                            "output": msg,
                            "arguments": args
                        }, agent.name)
                        
                        # Hafızaya ekle
                        agent.memory.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": func_name,
                            "content": msg
                        })
                        continue # Tool'u çalıştırma, sıradakine geç
                    # ---------------------------------------------------

                    # Tool Bul ve Çalıştır
                    if func_name in agent.tools:
                        
                        # UI Bildirimi
                        tool_func = agent.tools[func_name]
                        tmpl = getattr(tool_func, "_message_template", None)
                        
                        if not tmpl:
                             tmpl = f"Running {func_name} with {args}"

                        try:
                            msg = tmpl.format(**args)
                        except:
                            msg = tmpl
                        
                        yield AgentStreamEvent("tool_call_ready", [{
                            "function": {"name": func_name, "arguments": raw_args},
                            "message": msg
                        }], agent.name)

                        try:
                            # FONKSİYON ÇAĞRISI
                            result = agent.tools[func_name](**args)
                            result_str = str(result)
                        except Exception as e:
                            result_str = f"Error: {e}"
                    else:
                        result_str = f"Error: Tool {func_name} not found"

                    # Sonucu Event Olarak Fırlat
                    yield AgentStreamEvent("tool_result", {
                        "name": func_name, 
                        "output": result_str,
                        "arguments": args
                    }, agent.name)

                    # Sonucu HAFIZAYA EKLE
                    agent.memory.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": func_name,
                        "content": result_str
                    })

                # Döngü (step) başa döner, 'agent.memory' artık günceldir.
        
        finally:
            # 2. CALLER ID TEMİZLİĞİ: İş bitti, yığından çık.
            # Böylece bir üstteki fonksiyon (manager) tekrar "current_sender" olur.
            if self.agent_stack:
                self.agent_stack.pop()

            # 3. MIDDLEWARE: After Run
            for mw in self.middlewares:
                mw.after_run(agent, self)

    async def run_stream_async(self, agent: Agent, task: str, chat_history: List[Dict] = None) -> AsyncGenerator[AgentStreamEvent, None]:
        """
        Asenkron Çalıştırma Döngüsü (Async Support).
        """
        
        # 0. MIDDLEWARE: Before Run
        for mw in self.middlewares:
            # Async versiyonu çağır
            await mw.before_run_async(agent, self)

        self.agent_stack.append(agent.name)

        if not agent.memory:
            if agent.instructions:
                is_reasoning = self._is_reasoning_model(agent.model)
                if is_reasoning:
                    agent.memory.append({
                        "role": "user", 
                        "content": f"Instructions:\n{agent.system_prompt()}"
                    })
                else:
                    agent.memory.append({
                        "role": "system", 
                        "content": agent.system_prompt()
                    })
            if chat_history:
                agent.memory.extend(chat_history)

        agent.memory.append({"role": "user", "content": task})

        try:
            for step in range(agent.max_steps):
                tools = self._tool_schema(agent)

                try:
                    # ASYNC STREAM
                    stream = self.client.chat_stream_async(
                        model=agent.model,
                        messages=agent.memory,
                        tools=tools,
                        **agent.generation_config
                    )
                except Exception as e:
                    error_msg = str(e)
                    print(f"\nAPI ERROR ({agent.name}): {error_msg}")
                    yield AgentStreamEvent("error", error_msg, agent.name)
                    return

                current_content = ""
                current_tool_calls = {}
                
                async for event in stream:
                    event.agent_name = agent.name
                    
                    yield event

                    # --- MIDDLEWARE STREAM HOOK (ASYNC) ---
                    for mw in self.middlewares:
                        new_events = await mw.process_stream_event_async(event, agent, self)
                        if new_events:
                            for ne in new_events:
                                ne.agent_name = agent.name
                                yield ne
                    # --------------------------------------
                    
                    if event.type == "token":
                        current_content += str(event.data)
                        # yield event (Moved up)
                    
                    elif event.type == "reasoning":
                        # yield event (Moved up)
                        pass
                    
                    elif event.type == "tool_call":
                        tc_chunk = event.data
                        idx = tc_chunk.get("index", 0)
                        
                        if idx not in current_tool_calls:
                            current_tool_calls[idx] = {"id": tc_chunk.get("id"), "name": "", "arguments": ""}
                        
                        if "function" in tc_chunk:
                            fn = tc_chunk["function"]
                            if fn.get("name"): current_tool_calls[idx]["name"] = fn["name"]
                            if fn.get("arguments"): current_tool_calls[idx]["arguments"] += fn["arguments"]
                        
                        yield AgentStreamEvent("tool_call_ready", [tc_chunk], agent.name)

                assistant_msg = {"role": "assistant", "content": current_content if current_content else None}
                
                tool_calls_data = []
                if current_tool_calls:
                    for idx in sorted(current_tool_calls.keys()):
                        tc = current_tool_calls[idx]
                        tool_calls_data.append({
                            "id": tc.get("id") or f"call_{idx}_{step}",
                            "type": "function",
                            "function": {"name": tc["name"], "arguments": tc["arguments"]}
                        })
                    assistant_msg["tool_calls"] = tool_calls_data
                
                agent.memory.append(assistant_msg)

                if not tool_calls_data:
                    yield AgentStreamEvent("final", {"output": current_content}, agent.name)
                    return

                for tc in tool_calls_data:
                    call_id = tc["id"]
                    func_name = tc["function"]["name"]
                    raw_args = tc["function"]["arguments"]
                    
                    try:
                        args = json.loads(raw_args)
                    except:
                        args = {}

                    should_run = True
                    for mw in self.middlewares:
                        # Async hook'u çağır
                        # GÜNCELLEME: call_id eklendi
                        res = await mw.before_tool_execution_async(agent, self, func_name, args, call_id)
                        
                        if not res:
                            should_run = False
                            break
                    
                    if not should_run:
                        msg = f"Tool '{func_name}' execution was blocked by a middleware."
                        yield AgentStreamEvent("tool_result", {
                            "name": func_name, 
                            "output": msg,
                            "arguments": args
                        }, agent.name)
                        agent.memory.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": func_name,
                            "content": msg
                        })
                        continue

                    if func_name in agent.tools:
                        tool_func = agent.tools[func_name]
                        tmpl = getattr(tool_func, "_message_template", None)
                        if not tmpl: tmpl = f"Running {func_name} with {args}"
                        try: msg = tmpl.format(**args)
                        except: msg = tmpl
                        
                        yield AgentStreamEvent("tool_call_ready", [{
                            "function": {"name": func_name, "arguments": raw_args},
                            "message": msg
                        }], agent.name)

                        try:
                            # Tool ASYNC ise await et
                            if inspect.iscoroutinefunction(tool_func):
                                result = await tool_func(**args)
                            else:
                                result = tool_func(**args)
                            result_str = str(result)
                        except Exception as e:
                            result_str = f"Error: {e}"
                    else:
                        result_str = f"Error: Tool {func_name} not found"

                    yield AgentStreamEvent("tool_result", {
                        "name": func_name, 
                        "output": result_str,
                        "arguments": args
                    }, agent.name)

                    agent.memory.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": func_name,
                        "content": result_str
                    })
        
        finally:
            if self.agent_stack:
                self.agent_stack.pop()
            
            for mw in self.middlewares:
                # Async hook
                await mw.after_run_async(agent, self)