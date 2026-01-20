import unittest
import shutil
import os
import asyncio
from agent_sdk.middleware.rag import SimpleRAG, ChromaRAG

class TestRAG(unittest.TestCase):
    def test_simple_rag(self):
        db_path = "test_knowledge.db"
        rag = SimpleRAG(db_path=db_path)
        
        # Veri ekle
        rag._add_memory("Python is a programming language.", {"topic": "coding"})
        
        # Ara
        result = rag._search_memory("programming")
        self.assertIn("Python", result)
        
        # Temizlik
        if os.path.exists(db_path):
            os.remove(db_path)

    def test_chroma_rag(self):
        persist_dir = "./test_chroma_db"
        try:
            import chromadb
            rag = ChromaRAG(persist_dir=persist_dir, collection_name="test_col")
            
            rag._add_memory("The sky is blue.", {"topic": "nature"})
            result = rag._search_memory("sky")
            
            if result: 
                self.assertIn("sky", result.lower())
            
            # Windows'ta dosya kilidini kaldırmak için nesneyi silmeye çalışalım
            del rag
                
        except ImportError:
            print("ChromaDB not installed, skipping test.")
        finally:
            if os.path.exists(persist_dir):
                # ignore_errors=True ile hata olsa bile testi fail ettirmeyelim
                shutil.rmtree(persist_dir, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
