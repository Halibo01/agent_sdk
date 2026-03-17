import os

# Define Paths
SOURCE_FILE = r"..\agent_sdk_copy\agent_sdk	ools.py"

# Encrypted Keys
LANGSEARCH_ENC = "f963f4:c5d2g281bfd85be2345ge3b38.lt"
BRAVE_ENC = "msoQpiBsi.RGEhOpEdjoumpu`CYnBTC"

# The Helper Function Code to Insert
HELPER_FUNC = """
# --- SECURE KEY STORAGE ---
def _get_secure_key(encrypted):
    # Simple De-obfuscation: (Shift -1 -> Reverse)
    decrypted_chars = []
    for char in encrypted:
        decrypted_chars.append(chr(ord(char) - 1))
    return "".join(decrypted_chars)[::-1]
"""

def patch_tools():
    try:
        with open(SOURCE_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Insert Helper Function after imports (e.g., after 'load_dotenv()')
        if "_get_secure_key" not in content:
            content = content.replace("load_dotenv()", "load_dotenv()\n" + HELPER_FUNC, 1)

        # 2. Replace LangSearch Key Retrieval
        old_ls = 'api_key = os.getenv("LANGSEARCH_API_KEY")'
        new_ls = f'api_key = _get_secure_key("{LANGSEARCH_ENC}") # Obfuscated LANGSEARCH Key'
        content = content.replace(old_ls, new_ls)

        # 3. Replace BraveSearch Key Retrieval
        old_br = 'api_key = os.getenv("BRAVE_API_KEY")'
        new_br = f'api_key = _get_secure_key("{BRAVE_ENC}") # Obfuscated BRAVE Key'
        content = content.replace(old_br, new_br)

        with open(SOURCE_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        
        print("Successfully patched agent_sdk_copy/agent_sdk/tools.py with secure keys.")

    except Exception as e:
        print(f"Error patching file: {e}")

if __name__ == "__main__":
    patch_tools()
