"""
Runner Module

The `Runner` is the execution engine of the SDK. It manages the ReAct loop:
1. Sending messages to the LLM.
2. Parsing tool calls.
3. Executing tools (including middleware interception).
4. Feeding results back to the LLM.

Documentation: https://docs.agent-sdk-core.dev/modules/agents
"""

import json
import inspect
import asyncio
from typing import List, Dict, Any, Generator, AsyncGenerator, get_type_hints, Optional
from .agent import Agent
from .events import AgentStreamEvent

# 1. TYPE MAP (Python -> JSON Schema)
PYTHON_TO_JSON = {
    int: "integer",
    float: "number",
    str: "string",
    bool: "boolean",
    list: "array",
    dict: "object"
}

# 2. SPECIAL MODELS (Reasoning/Thinking)
# These models cannot use Tools and do not like System Prompts.
REASONING_KEYWORDS = [
    "o1-", "o1-mini", "o1-preview", 
    "r1", "reasoner", "think", 
    "chimera", "deepseek-r1"
]

class Runner:
    def __init__(self, client):
        self.client = client
        self.agent_stack = ["User"]
        self.middlewares = []

    def use(self, middleware):
        """Adds a middleware to the Runner."""
        self.middlewares.append(middleware)

    @property
    def current_sender(self) -> str:
        """Returns the name of the agent currently invoking this function (Active)."""
        return self.agent_stack[-1] if self.agent_stack else "User"

    def _is_reasoning_model(self, model_name: str) -> bool:
        """Checks if the model supports tools."""
        return any(keyword in model_name.lower() for keyword in REASONING_KEYWORDS)

    def _prepare_messages(self, agent: Agent, input_text: str, history: List[Dict]) -> List[Dict]:
        """
        Converts 'system' role to 'user' for reasoning models.
        Sets up standard structure for normal models.
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

        # 2. Add History
        if history:
            messages.extend(history)

        # 3. New Input
        messages.append({"role": "user", "content": input_text})
        
        return messages

    def _parse_text_for_tool_calls(self, text: str) -> List[Dict]:
        """
        Parses raw text to find tool calls. This acts as a ReAct parser for local models 
        that do not support native API tool calling (e.g. Qwen XML format or Markdown JSON).
        """
        if not text: return []
        tool_calls = []
        import re
        import json
        import uuid

        # 1. Check for Qwen-style XML tool calls: <tool_call>\n<function=name>\n<parameter=key>val</parameter>\n</function>\n</tool_call>
        if "<tool_call>" in text:
            tool_blocks = re.findall(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL)
            for block in tool_blocks:
                func_match = re.search(r"<function=([^>]+)>", block)
                if func_match:
                    func_name = func_match.group(1).strip()
                    args = {}
                    param_blocks = re.findall(r"<parameter=([^>]+)>(.*?)</parameter>", block, re.DOTALL)
                    for p_name, p_val in param_blocks:
                        args[p_name.strip()] = p_val.strip()
                    
                    tool_calls.append({
                        "id": f"call_{uuid.uuid4().hex[:8]}",
                        "type": "function",
                        "function": {"name": func_name, "arguments": json.dumps(args)}
                    })
        
        # 2. Check for standard Markdown JSON blocks
        if not tool_calls and "```json" in text:
            json_blocks = re.findall(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    if isinstance(data, dict) and "name" in data:
                        args_key = "arguments" if "arguments" in data else "parameters" if "parameters" in data else None
                        if args_key:
                            tool_calls.append({
                                "id": f"call_{uuid.uuid4().hex[:8]}",
                                "type": "function",
                                "function": {
                                    "name": data["name"], 
                                    "arguments": json.dumps(data[args_key]) if isinstance(data[args_key], dict) else data[args_key]
                                }
                            })
                except (json.JSONDecodeError, ValueError, KeyError, TypeError):
                    pass

        # 3. Fallback: Check for raw JSON without markdown blocks (like Llama-3 or Mistral)
        text_clean = text.strip()
        if not tool_calls and (text_clean.startswith("{") or text_clean.startswith("[")):
            try:
                parsed_data = json.loads(text_clean)
                # Mistral outputs a list of tool calls: [{"name": "...", "arguments": {...}}]
                if isinstance(parsed_data, list):
                    items = parsed_data
                else:
                    items = [parsed_data]
                    
                for data in items:
                    if isinstance(data, dict) and "name" in data:
                        args_key = "arguments" if "arguments" in data else "parameters" if "parameters" in data else None
                        if args_key:
                            tool_calls.append({
                                "id": f"call_{uuid.uuid4().hex[:8]}",
                                "type": "function",
                                "function": {
                                    "name": data["name"], 
                                    "arguments": json.dumps(data[args_key]) if isinstance(data[args_key], dict) else data[args_key]
                                }
                            })
            except (json.JSONDecodeError, ValueError, KeyError, TypeError):
                pass

        return tool_calls

    def _tool_schema(self, agent: Agent) -> Optional[List[Dict]]:
        """
        Converts agent's functions to JSON schema.
        Does not send Tools if model is reasoning.
        """
        # A) Reasoning Models Cannot Use Tools
        if self._is_reasoning_model(agent.model):
            return None

        # B) Return None if No Tools
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
        Main Execution Loop (Persistent Memory Supported).
        """
        
        for mw in self.middlewares:
            mw.before_run(agent, self)

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
            # Infinite loop protection
            for step in range(agent.max_steps):
                
                tools = self._tool_schema(agent)

                try:
                    stream = self.client.chat_stream(
                        model=agent.model,
                        messages=agent.memory,
                        tools=tools,
                        **agent.generation_config
                    )
                except Exception as e:
                    error_msg = str(e)
                    if hasattr(e, 'response') and e.response is not None:
                        # Add detailed error from API
                        error_msg += f"\nServer Response: {e.response.text}"
                    
                    print(f"\nAPI ERROR ({agent.name}): {error_msg}")
                    yield AgentStreamEvent("error", error_msg, agent.name)
                    return

                current_content = ""
                current_tool_calls = {}
                
                # Stream hiding state
                text_buffer = ""
                hiding_output = False
                
                # --- STREAM LOOP ---
                for raw_event in stream:
                    # We create a new event to avoid mutating the original if it's cached
                    event = AgentStreamEvent(raw_event.type, raw_event.data, agent.name)

                    if event.type == "token":
                        chunk = str(event.data)
                        current_content += chunk
                        text_buffer += chunk
                        
                        if not hiding_output:
                            # Check if we might be entering a tool call block
                            if "<tool_call>" in text_buffer or "```json" in text_buffer:
                                hiding_output = True
                                # Find where it started to yield the text before it
                                split_idx = text_buffer.find("<tool_call>")
                                if split_idx == -1: split_idx = text_buffer.find("```json")
                                
                                if split_idx > 0:
                                    safe_text = text_buffer[:split_idx]
                                    event.data = safe_text
                                    yield event
                                    
                                # Keep the rest in buffer to track when it ends
                                text_buffer = text_buffer[split_idx:]
                                continue
                                
                            # Check for raw JSON tool calls (like Llama 3) e.g. {"name": ...} or [{"name": ...}]
                            elif current_content.strip().startswith('{"name":') or current_content.strip().startswith('[{"name":'):
                                hiding_output = True
                                text_buffer = current_content # hide everything
                                continue
                                
                            elif "<" in text_buffer or "`" in text_buffer or (current_content.strip() in ["{", '{"', '{"n', '{"na', '{"nam', '{"name', "[", '[{', '[{"', '[{"n', '[{"na', '[{"nam', '[{"name']):
                                # Might be the start of a tag or raw json tool call, hold it briefly (max 15 chars)
                                if len(text_buffer) < 20:
                                    continue
                                
                            # Safe to yield
                            event.data = text_buffer
                            yield event
                            text_buffer = ""
                            
                        else:
                            # We are hiding output. Wait for the closing tags.
                            if "</tool_call>" in text_buffer or (text_buffer.count("```") >= 2):
                                hiding_output = False
                                # Find where it ended
                                end_idx = text_buffer.find("</tool_call>")
                                if end_idx != -1:
                                    text_buffer = text_buffer[end_idx + 12:]
                                else:
                                    # For json block, find the second ```
                                    first_idx = text_buffer.find("```")
                                    second_idx = text_buffer.find("```", first_idx + 3)
                                    text_buffer = text_buffer[second_idx + 3:]
                            continue
                            
                    else:
                        yield event

                    # --- MIDDLEWARE STREAM HOOK ---
                    for mw in self.middlewares:
                        new_events = mw.process_stream_event(event, agent, self)
                        if new_events:
                            for ne in new_events:
                                ne.agent_name = agent.name
                                yield ne
                    # ------------------------------
                    
                    if event.type == "reasoning":
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

                # Yield any remaining safe text in buffer
                if text_buffer and not hiding_output:
                    yield AgentStreamEvent("token", text_buffer, agent.name)

                # --- DECISION MOMENT (END OF LOOP) ---
                
                # Clean the raw XML/JSON from the memory so the agent's history is clean
                clean_memory_content = current_content
                import re
                clean_memory_content = re.sub(r"<tool_call>.*?</tool_call>", "", clean_memory_content, flags=re.DOTALL)
                clean_memory_content = re.sub(r"```json.*?```", "", clean_memory_content, flags=re.DOTALL)
                clean_memory_content = clean_memory_content.strip()

                assistant_msg = {"role": "assistant", "content": clean_memory_content if clean_memory_content else None}
                
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
                else:
                    # Fallback for Local/GGUF models that output tools as text (XML or JSON)
                    text_tools = self._parse_text_for_tool_calls(current_content)
                    if text_tools:
                        tool_calls_data = text_tools
                        # For history correctness, we tell the API this was a tool call
                        assistant_msg["tool_calls"] = tool_calls_data
                
                agent.memory.append(assistant_msg)

                # 2. IF No Tool Calls -> FINISH
                if not tool_calls_data:
                    yield AgentStreamEvent("final", {"output": current_content}, agent.name)
                    return

                # 3. IF Tools -> EXECUTE
                for tc in tool_calls_data:
                    call_id = tc["id"]
                    func_name = tc["function"]["name"]
                    raw_args = tc["function"]["arguments"]
                    
                    try:
                        args = json.loads(raw_args)
                    except (json.JSONDecodeError, ValueError):
                        args = {}

                    # --- MIDDLEWARE CHECK (Human-in-the-loop etc.) ---
                    should_run = True
                    for mw in self.middlewares:
                        # If a middleware returns False, break chain and do not execute
                        # UPDATE: call_id added
                        if not mw.before_tool_execution(agent, self, func_name, args, call_id):
                            should_run = False
                            break
                    
                    if not should_run:
                        msg = f"Tool '{func_name}' execution was blocked by a middleware."
                        print(f"\n{msg}")
                        
                        # Notify User
                        yield AgentStreamEvent("tool_result", {
                            "name": func_name, 
                            "output": msg,
                            "arguments": args
                        }, agent.name)
                        
                        # Add to Memory
                        agent.memory.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": func_name,
                            "content": msg
                        })
                        continue # Do not execute tool, skip to next
                    # ---------------------------------------------------

                    # Find and Execute Tool
                    if func_name in agent.tools:
                        
                        # UI Notification
                        tool_func = agent.tools[func_name]
                        tmpl = getattr(tool_func, "_message_template", None)
                        
                        if not tmpl:
                             tmpl = f"Running {func_name} with {args}"

                        try:
                            msg = tmpl.format(**args)
                        except (KeyError, IndexError, ValueError):
                            msg = tmpl

                        yield AgentStreamEvent("tool_call_ready", [{
                            "function": {"name": func_name, "arguments": raw_args},
                            "message": msg
                        }], agent.name)

                        try:
                            # FUNCTION CALL
                            tool_func = agent.tools[func_name]
                            if inspect.iscoroutinefunction(tool_func):
                                try:
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        import concurrent.futures
                                        with concurrent.futures.ThreadPoolExecutor() as pool:
                                            result = pool.submit(asyncio.run, tool_func(**args)).result()
                                    else:
                                        result = loop.run_until_complete(tool_func(**args))
                                except RuntimeError:
                                    result = asyncio.run(tool_func(**args))
                            else:
                                result = tool_func(**args)
                            result_str = str(result)
                        except Exception as e:
                            result_str = f"Error: {e}"
                    else:
                        result_str = f"Error: Tool {func_name} not found"

                    # Yield Result as Event
                    yield AgentStreamEvent("tool_result", {
                        "name": func_name, 
                        "output": result_str,
                        "arguments": args
                    }, agent.name)

                    # ADD Result to MEMORY
                    agent.memory.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": func_name,
                        "content": result_str
                    })

                # Loop (step) restarts, 'agent.memory' is now up to date.
        
        finally:
            # 2. CALLER ID CLEANUP: Job done, pop from stack.
            # So the parent function (manager) becomes "current_sender" again.
            if self.agent_stack:
                self.agent_stack.pop()

            # 3. MIDDLEWARE: After Run
            for mw in self.middlewares:
                mw.after_run(agent, self)

    async def run_stream_async(self, agent: Agent, task: str, chat_history: List[Dict] = None) -> AsyncGenerator[AgentStreamEvent, None]:
        """
        Asynchronous Execution Loop (Async Support).
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

                text_buffer = ""
                hiding_output = False

                async for event in stream:
                    event.agent_name = agent.name

                    if event.type == "token":
                        chunk = str(event.data)
                        current_content += chunk
                        text_buffer += chunk

                        if not hiding_output:
                            # Check if we might be entering a tool call block
                            if "<tool_call>" in text_buffer or "```json" in text_buffer:
                                hiding_output = True
                                split_idx = text_buffer.find("<tool_call>")
                                if split_idx == -1: split_idx = text_buffer.find("```json")

                                if split_idx > 0:
                                    safe_text = text_buffer[:split_idx]
                                    event.data = safe_text
                                    yield event

                                text_buffer = text_buffer[split_idx:]
                                continue

                            elif current_content.strip().startswith('{"name":') or current_content.strip().startswith('[{"name":'):
                                hiding_output = True
                                text_buffer = current_content
                                continue

                            elif "<" in text_buffer or "`" in text_buffer or (current_content.strip() in ["{", '{"', '{"n', '{"na', '{"nam', '{"name', "[", '[{', '[{"', '[{"n', '[{"na', '[{"nam', '[{"name']):
                                if len(text_buffer) < 20:
                                    continue

                            event.data = text_buffer
                            yield event
                            text_buffer = ""

                        else:
                            if "</tool_call>" in text_buffer or (text_buffer.count("```") >= 2):
                                hiding_output = False
                                end_idx = text_buffer.find("</tool_call>")
                                if end_idx != -1:
                                    text_buffer = text_buffer[end_idx + 12:]
                                else:
                                    first_idx = text_buffer.find("```")
                                    second_idx = text_buffer.find("```", first_idx + 3)
                                    text_buffer = text_buffer[second_idx + 3:]
                            continue
                    else:
                        yield event

                    # --- MIDDLEWARE STREAM HOOK (ASYNC) ---
                    for mw in self.middlewares:
                        new_events = await mw.process_stream_event_async(event, agent, self)
                        if new_events:
                            for ne in new_events:
                                ne.agent_name = agent.name
                                yield ne
                    # --------------------------------------

                    if event.type == "reasoning":
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

                # Yield any remaining safe text in buffer
                if text_buffer and not hiding_output:
                    yield AgentStreamEvent("token", text_buffer, agent.name)

                # Clean the raw XML/JSON from the memory so the agent's history is clean
                clean_memory_content = current_content
                import re
                clean_memory_content = re.sub(r"<tool_call>.*?</tool_call>", "", clean_memory_content, flags=re.DOTALL)
                clean_memory_content = re.sub(r"```json.*?```", "", clean_memory_content, flags=re.DOTALL)
                clean_memory_content = clean_memory_content.strip()

                assistant_msg = {"role": "assistant", "content": clean_memory_content if clean_memory_content else None}
                
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
                else:
                    # Fallback for Local/GGUF models that output tools as text (XML or JSON)
                    text_tools = self._parse_text_for_tool_calls(current_content)
                    if text_tools:
                        tool_calls_data = text_tools
                        # For history correctness, we tell the API this was a tool call
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
                    except (json.JSONDecodeError, ValueError):
                        args = {}

                    should_run = True
                    for mw in self.middlewares:
                        # Call async hook
                        # UPDATE: call_id added
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
                        except (KeyError, IndexError, ValueError): msg = tmpl
                        
                        yield AgentStreamEvent("tool_call_ready", [{
                            "function": {"name": func_name, "arguments": raw_args},
                            "message": msg
                        }], agent.name)

                        try:
                            # If tool is ASYNC, await it
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