"""
Built-in Tools

Standard tools provided by the SDK for common tasks like file I/O, web search, and code execution.

Documentation: https://docs.agent-sdk-core.dev/modules/tools

Key Tools:
- **FileSystem**: `read_file`, `save_file`, `list_directory`
- **Web**: `web_search`, `visit_webpage`, `wikipedia_search`
- **Execution**: `run_python_code`, `execute_command`
- **Utility**: `get_current_time`

To create custom tools, use the `@tool_message` decorator.
"""

import json
import os
import subprocess
import asyncio
import datetime
import math
import re
import random
import requests
from dotenv import load_dotenv
from markdownify import markdownify as tomd
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urlunparse

# --- OPTIONAL DEPENDENCIES (LAZY IMPORTS) ---
# This prevents the SDK from crashing if optional tools are not installed.

try:
    from duckduckgo_search import DDGS
    _HAS_DDGS = True
except ImportError:
    _HAS_DDGS = False

try:
    import wikipedia
    _HAS_WIKIPEDIA = True
except ImportError:
    _HAS_WIKIPEDIA = False

from .decorators import tool_message, approval_required
from .sandbox import DockerSandbox, LocalSandbox
from .utils import *

load_dotenv()

# --- SANDBOX ENVIRONMENT SETUP ---

# Default libraries and variables available to an agent without imports
STANDARD_GLOBALS = {
    "math": math,
    "datetime": datetime,
    "json": json,
    "re": re,
    "random": random,
    "os": os, # May pose security risk but included for convenience
    "print": print, # Already built-in but explicit inclusion causes no harm
}

# Sandbox Selector Logic
_docker_sandbox = DockerSandbox()
_local_sandbox = LocalSandbox(custom_globals=STANDARD_GLOBALS)

def get_sandbox():
    """Return Docker sandbox if available, otherwise return Local sandbox."""
    if _docker_sandbox.is_available():
        return _docker_sandbox
    return _local_sandbox

@tool_message("Searching '{query}' on web...")
def web_search(query: str) -> str:
    """
    Search the web using DuckDuckGo.
    Use this for current events, news, and general information.
    """
    if not _HAS_DDGS:
        return "Error: 'duckduckgo-search' is not installed. Please install it with `pip install agent_sdk[tools]`."

    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(f"Title: {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}")
        
        if not results:
            return "No results found."
            
        return "\n\n".join(results)
    except Exception as e:
        return f"Error during search: {str(e)}"
    


@tool_message("Searching '{query}' on wikipedia...")
def wikipedia_search(query: str, lang: str = "tr") -> str:
    """
    Search for detailed information on Wikipedia.
    The `lang` parameter can be in any language.
    """
    if not _HAS_WIKIPEDIA:
        return "Error: 'wikipedia' module is not installed. Please install it with `pip install agent_sdk[tools]`."

    try:
        wikipedia.set_lang(lang)
        # First search and pick the best result
        search_results = wikipedia.search(query)
        if not search_results:
            return "No relevant Wikipedia title found."
        
        # Fetch the summary of the top result
        page = wikipedia.page(search_results[0], auto_suggest=False)
        return f"Title: {page.title}\nSummary: {page.summary[:1000]}..." # First 1000 characters
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Search is ambiguous, did you mean one of these? {e.options[:5]}"
    except Exception as e:
        return f"Wikipedia error: {str(e)}"

# --- 3. SYSTEM TIME (Time Awareness) ---
@tool_message("Checking system time...")
def get_current_time() -> str:
    """
    Return the current date and time. Useful for answering "What day is it today?".
    """
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S (%A)")

# --- 4. FILE SYSTEM TOOLS ---

@tool_message("Listing directory contents of '{path}'")
def list_directory(path: str = ".") -> str:
    """
    List files and directories in the specified path.
    Args:
        path: Directory path (default is current directory).
    """
    try:
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."
        
        items = os.listdir(path)
        # Add indicators for directories
        result = []
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                result.append(f"[DIR]  {item}")
            else:
                result.append(f"[FILE] {item}")
        
        return "\n".join(result)
    except Exception as e:
        return f"Error listing directory: {e}"

@tool_message("Reading file '{path}'")
def read_file(path: str) -> str:
    """
    Read the content of a text file.
    Note: Reads max 20,000 characters to prevent memory issues.
    """
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file."

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(20000) # Safety limit
            if len(content) == 20000:
                content += "\n...[TRUNCATED: File too large]..."
            return content
    except Exception as e:
        return f"Error reading file: {e}"

# --- 5. SYSTEM COMMAND EXECUTION ---

@approval_required
@tool_message("Executing command: '{command}'")
def execute_command(command: str) -> str:
    """
    Execute a shell command safely.
    Requires Human Approval.
    Captures stdout and stderr. Timeout is 30 seconds.
    """
    try:
        # shell=True is risky but necessary for complex commands.
        # We rely on @approval_required middleware for safety.
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
            
        if not output:
            output = "(Command executed with no output)"
            
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing command: {e}"

# --- 6. SANDBOXED CODE EXECUTION ---

@approval_required
@tool_message("Running Python code in sandbox...")
def run_python_code(code: str) -> str:
    """
    Execute Python code in a secure sandbox environment.
    Automatically chooses Docker (if available) or a restricted local process.
    Pre-loaded libraries: math, datetime, json, re, random, os.
    """
    sandbox = get_sandbox()
    return sandbox.run_code(code)

@approval_required
@tool_message("Running Python code in sandbox (Async)...")
async def run_python_code_async(code: str) -> str:
    """
    Execute Python code in a secure sandbox environment asynchronously.
    """
    sandbox = get_sandbox()
    return await sandbox.run_code_async(code)


# --- ASYNC VERSIONS ---
@approval_required
@tool_message("Listing directory contents of '{path}' (Async)")
async def list_directory_async(path: str = ".") -> str:
    """
    List files and directories in the specified path asynchronously.
    """
    return await asyncio.to_thread(list_directory, path)

@tool_message("Reading file '{path}' (Async)")
async def read_file_async(path: str) -> str:
    """
    Read the content of a text file asynchronously.
    """
    return await asyncio.to_thread(read_file, path)

@approval_required
@tool_message("Executing command: '{command}' (Async)")
async def execute_command_async(command: str) -> str:
    """
    Execute a shell command safely and asynchronously.
    Requires Human Approval.
    """
    try:
        # Create subprocess
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for output with timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        except asyncio.TimeoutExpired:
            process.kill()
            return "Error: Command timed out after 30 seconds."

        output = ""
        if stdout:
            output += f"STDOUT:\n{stdout.decode(errors='replace')}\n"
        if stderr:
            output += f"STDERR:\n{stderr.decode(errors='replace')}\n"
            
        if not output:
            output = "(Command executed with no output)"
            
        return output
    except Exception as e:
        return f"Error executing command: {e}"

    

@tool_message("Visiting '{url}'")
def VisitWebpage(url:str):
    """
    Visit a webpage legally and return its markdown-converted content.
    If robots.txt restricts access, returns a restricted message.

    Args:
        url (str): Full URL of the website to visit.

    Returns:
        str: Markdown content of the webpage, or "<url> is restricted"
            if robots.txt disallows scraping.
    """
    webpage = safe_scrape(url)
    if webpage:
        mdwebpage = tomd(webpage)
        return mdwebpage
    else:
        return f"{url} is restricted"




@tool_message("Making langsearch as '{q}'")
def LangSearch(q:str, website_count:int = 5):
        api_key = os.getenv("LANGSEARCH_API_KEY")
        if not api_key:
            return "Error: LANGSEARCH_API_KEY environment variable is not set."

        url = "https://api.langsearch.com/v1/web-search"

        payload = json.dumps({
        "query": q,
        "freshness": "noLimit",
        "summary": True,
        "count": website_count,
        })
        headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        json_response = response.json()
        all_webpages = json_response["data"]["webPages"]["value"]
        webpages = {"webpages":[]}
        for i in all_webpages:
            webpages["webpages"].append(
                {
                    "name":i["name"], 
                    "url":i["url"], 
                    "snippet":i["snippet"], 
                    "summary":i["summary"][:800] + "...",
                    "datePublished":i["datePublished"],
                    "is_scrapable":is_scrapable(i["url"])
                }
            )
        

        
        return str(webpages)

@tool_message("Making langsearch as '{q}' (Async)")
async def LangSearch_async(q:str, website_count:int = 5):
    """
    Asynchronous wrapper for LangSearch.
    """
    return await asyncio.to_thread(LangSearch, q, website_count)


@tool_message("Visiting '{url}' (Async)")
async def VisitWebpage_async(url:str):
    """
    Asynchronous wrapper for VisitWebpage.
    """
    return await asyncio.to_thread(VisitWebpage, url)



@tool_message("Making brave search as '{q}'")
def BraveSearch(q: str, website_count: int = 5):
    """
    Perform a web search using Brave Search API.
    Returns structured results similar to LangSearch.
    """
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        return "Error: BRAVE_API_KEY environment variable is not set."

    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key
    }
    params = {"q": q, "count": website_count}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("web", {}).get("results", [])
        webpages = {"webpages": []}

        for item in results:
            # Brave doesn't always give a long summary, so we use description.
            # We also check scrapability (simulated based on typical bot rules or helper)
            item_url = item.get("url", "")
            
            webpages["webpages"].append({
                "name": item.get("title", ""),
                "url": item_url,
                "snippet": item.get("description", ""), # Brave's snippet
                "summary": item.get("description", "")[:800] + "...", # Same as snippet for now
                "datePublished": item.get("age", ""), # Brave provides 'age' sometimes
                "is_scrapable": is_scrapable(item_url)
            })
            
        return str(webpages)

    except Exception as e:
        return f"Error during Brave Search: {e}"

@tool_message("Making brave search as '{q}' (Async)")
async def BraveSearch_async(q: str, website_count: int = 5):
    """
    Asynchronous wrapper for BraveSearch.
    """
    return await asyncio.to_thread(BraveSearch, q, website_count)


@tool_message("Saving content to '{filename}'")
def save_file(filename:str, content:str) -> str:
    """
    Saves the given text as a file. It could be a .txt file or .md file.
    args:
        filename (str): file name or full path for a file. Example: 'save_it.txt'.

    Returns:
        str: <filename full path> created successfully.
    Exception:
        str: File could't be created. Error: <error type>
    """
    try:
        if not filename.endswith(".md") or not filename.endswith(".txt"):
            return f"File must be a .txt file or a .md file. '{filename}' is unacceptable"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File created successfully. File path is '{os.path.abspath(filename)}'."
    except Exception as e:
        return f"File couldn't be created. Error: {e}"

@tool_message("Reading uploaded file '{filename}'")
def read_uploaded_file(filename: str) -> str:
    """
    Reads a file exclusively from the 'uploads' directory.
    Prevents 'Path Traversal' attacks by verifying the resolved path.
    """
    upload_dir = os.path.abspath("uploads")
    requested_path = os.path.abspath(os.path.join(upload_dir, filename))

    # SECURITY CHECK: Path Traversal Prevention
    # Ensure the requested path actually starts with the uploads directory path.
    if not requested_path.startswith(upload_dir):
        return f"Security Error: Access denied. You can only read files inside '{upload_dir}'."
    
    if not os.path.exists(requested_path):
        return f"Error: File '{filename}' not found in uploads."

    try:
        with open(requested_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"