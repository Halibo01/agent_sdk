import unittest
import os
import shutil
import asyncio
from agent_sdk.tools import list_directory, read_file, execute_command, list_directory_async

class TestTools(unittest.TestCase):
    def setUp(self):
        # Test için geçici bir klasör oluştur
        self.test_dir = "temp_test_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        with open(f"{self.test_dir}/hello.txt", "w") as f:
            f.write("Hello World")

    def tearDown(self):
        # Temizlik
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_list_directory(self):
        result = list_directory(self.test_dir)
        self.assertIn("hello.txt", result)
        self.assertIn("[FILE]", result)

    def test_read_file(self):
        content = read_file(f"{self.test_dir}/hello.txt")
        self.assertEqual(content, "Hello World")

    def test_execute_command(self):
        # Bu test HumanInTheLoop onayı gerektireceği için mocklanmalıdır 
        # veya approval devre dışı bırakılmalıdır. 
        # Şimdilik basitçe echo komutunu deneyelim (Approval middleware test ortamında by-pass edilmeli)
        pass 

if __name__ == "__main__":
    unittest.main()
