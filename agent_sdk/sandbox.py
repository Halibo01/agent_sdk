import abc
import subprocess
import sys
import os
import tempfile
import asyncio
import shutil
import ast
import io
import contextlib
import traceback
from typing import Dict, Any, Optional

class BaseSandbox(abc.ABC):
    @abc.abstractmethod
    def run_code(self, code: str, timeout: int = 30) -> str:
        pass

    @abc.abstractmethod
    async def run_code_async(self, code: str, timeout: int = 30) -> str:
        pass

class LocalSandbox(BaseSandbox):
    """
    Docker olmayan ortamlar için 'In-Process' kod çalıştırıcı.
    Kodu doğrudan 'exec()' ile çalıştırır.
    """
    
    def __init__(self, custom_globals: Optional[Dict[str, Any]] = None):
        """
        Args:
            custom_globals: Kodun erişebileceği hazır fonksiyonlar ve değişkenler.
                            Örn: {'my_func': my_func, 'pd': pandas}
        """
        # Kodların çalışacağı global namespace (hafıza).
        # Standart __builtins__ dışında, kullanıcının verdiği özel objeleri ekliyoruz.
        self.globals = {}
        self.locals = {}
        
        # Güvenli builtins (İsteğe bağlı kısıtlanabilir ama şimdilik standart bırakıyoruz)
        # self.globals['__builtins__'] = __builtins__
        
        if custom_globals:
            self.globals.update(custom_globals)

    def run_code(self, code: str, timeout: int = 30) -> str:
        """
        Kodu doğrudan mevcut process içinde çalıştırır ve çıktıyı yakalar.
        """
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
                # Kodu çalıştır
                exec(code, self.globals, self.locals)
            
            output = ""
            stdout_val = stdout_buffer.getvalue()
            stderr_val = stderr_buffer.getvalue()

            if stdout_val:
                output += f"{stdout_val}\n"
            if stderr_val:
                output += f"ERROR/STDERR:\n{stderr_val}\n"
            
            if not output.strip():
                return "(Code executed successfully with no output)"
            
            return output.strip()

        except Exception:
            return f"Execution Error:\n{traceback.format_exc()}"

    async def run_code_async(self, code: str, timeout: int = 30) -> str:
        """
        Kodu asenkron olarak (thread içinde) çalıştırır.
        """
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self.run_code, code, timeout),
                timeout=timeout
            )
        except asyncio.TimeoutExpired:
            return "Error: Execution timed out (Thread is still running in background)."
        except Exception as e:
            return f"Async Execution Error: {e}"


class DockerSandbox(BaseSandbox):
    """
    Docker tabanlı tam izole sandbox.
    Gereksinim: Sistemde Docker yüklü olmalı ve 'docker-py' kütüphanesi bulunmalı.
    """
    def __init__(self, image: str = "python:3.9-slim"):
        self.image = image
        try:
            import docker
            self.client = docker.from_env()
        except ImportError:
            self.client = None
            print("[DockerSandbox] Warning: 'docker' library not found. Please install via 'pip install docker'")
        except Exception as e:
            self.client = None
            print(f"[DockerSandbox] Warning: Could not connect to Docker daemon: {e}")

    def is_available(self):
        return self.client is not None

    def run_code(self, code: str, timeout: int = 30) -> str:
        if not self.client:
            return "Error: Docker not available."
        
        try:
            container = self.client.containers.run(
                self.image,
                command=["python", "-c", code],
                mem_limit="128m", # Hafıza limiti
                nano_cpus=500000000, # 0.5 CPU
                network_disabled=True, # İnterneti kes
                remove=True, # İş bitince sil
                detach=False, # Bekle
                stdout=True,
                stderr=True
            )
            return container.decode("utf-8")
        except Exception as e:
            return f"Docker Error: {e}"

    async def run_code_async(self, code: str, timeout: int = 30) -> str:
        # Docker SDK'sı genelde senkrondur, bu yüzden thread'e atıyoruz.
        return await asyncio.to_thread(self.run_code, code, timeout)

class SecurityError(Exception):
    pass
