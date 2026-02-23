import subprocess
import tempfile
import os
import json

class StaticAnalyzer:
    @staticmethod
    def run_analysis(code_string: str) -> dict:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            tmp.write(code_string.encode('utf-8'))
            tmp_path = tmp.name

        try:
            return {
                "pylint_issues": StaticAnalyzer._get_pylint_data(tmp_path),
                "complexity": StaticAnalyzer._get_radon_data(tmp_path)
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
    def _get_pylint_data(file_path: str) -> list:
        try:
            cmd = ["pylint", "--errors-only", "--output-format=json", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            data = json.loads(result.stdout)
            return [{"line": i['line'], "msg": i['message']} for i in data]
        except Exception:
            return []

    @staticmethod
    def _get_radon_data(file_path: str) -> list:
        try:
            cmd = ["radon", "cc", "-s", "--json", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            data = json.loads(result.stdout)
            file_key = list(data.keys())[0]
            return [{"name": i['name'], "score": i['complexity']} for i in data[file_key] if i['complexity'] > 5]
        except Exception:
            return []