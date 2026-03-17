import os
import time
from agent_sdk.tools import search_inside_document, recursive_document_analysis

def test_large_files():
    pdf_path = r"C:\Users\Asus\Downloads\test\bme-fundamental-bronzino.pdf"
    txt_path = r"C:\Users\Asus\Downloads\test\pg70364.txt"
    
    print("=" * 60)
    print("TEST 1: In-Memory Semantic Search on 13.6 MB PDF")
    print("=" * 60)
    if os.path.exists(pdf_path):
        query = "What is the definition of biomedical engineering or biomaterials?"
        print(f"File: {os.path.basename(pdf_path)}\nQuery: '{query}'")
        start = time.time()
        # This will extract text from PDF, chunk it, embed it in RAM, and search
        result = search_inside_document(pdf_path, query, top_k=2)
        end = time.time()
        print(f"\nTime taken: {end - start:.2f} seconds")
        print("Result:\n")
        print(result)
    else:
        print(f"File not found: {pdf_path}")

    print("\n" + "=" * 60)
    print("TEST 2: Recursive Analysis (Rolling State) on 41 KB TXT")
    print("=" * 60)
    if os.path.exists(txt_path):
        query = "Summarize the main topic, events, or characters of this document."
        print(f"File: {os.path.basename(txt_path)}\nQuery: '{query}'")
        start = time.time()
        result = recursive_document_analysis(txt_path, query)
        end = time.time()
        print(f"\nTime taken: {end - start:.2f} seconds")
        print("Result:\n")
        print(result)
    else:
        print(f"File not found: {txt_path}")

if __name__ == "__main__":
    if not os.environ.get("OPENROUTER_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        print("API keys not set. Please set OPENROUTER_API_KEY or GEMINI_API_KEY.")
    else:
        try:
            import PyPDF2
        except ImportError:
            print("PyPDF2 is missing. The PDF test will fail. Please run 'pip install PyPDF2' first.")
            
        test_large_files()
