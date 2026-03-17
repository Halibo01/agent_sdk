import os
import time
from agent_sdk.tools import recursive_document_analysis

def run_test():
    print("--- Testing Recursive Document Analysis ---")
    
    # 1. Create a dummy large document
    filename = "dummy_large_doc.txt"
    content = ""
    for i in range(1, 101):
        if i == 42:
            content += f"Paragraph {i}: The secret password to access the vault is 'ORANGE_BANANA_77'.\n\n"
        elif i == 88:
            content += f"Paragraph {i}: The suspect was seen escaping in a blue van.\n\n"
        else:
            content += f"Paragraph {i}: Just some random filler text that doesn't matter much. The weather is nice today.\n\n"
            
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Created '{filename}' with {len(content)} characters.")
    
    # 2. Test 1: Find the password
    print("\n[Test 1] Searching for the password...")
    start = time.time()
    result1 = recursive_document_analysis(filename, "What is the secret password to the vault?")
    end = time.time()
    print(f"Result (took {end-start:.2f}s):\n{result1}")
    
    # 3. Test 2: Find the suspect vehicle
    print("\n[Test 2] Searching for suspect info...")
    result2 = recursive_document_analysis(filename, "How did the suspect escape? Describe the vehicle.")
    print(f"Result:\n{result2}")
    
    # Cleanup
    os.remove(filename)
    print("\nTest finished and cleaned up.")

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("OPENROUTER_API_KEY"):
        print("Please set OPENROUTER_API_KEY or GEMINI_API_KEY to run this test.")
    else:
        run_test()
