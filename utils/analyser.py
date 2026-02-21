import subprocess
import tempfile
import os
import json
from typing import Dict

class StaticAnalyzer:
    @staticmethod
    def run_analysis(code_string: str) -> Dict:
        """
        Runs Pylint and Radon on a code string using a temporary file.
        Returns critical flags for Logic and Complexity.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            tmp.write(code_string.encode('utf-8'))
            tmp_path = tmp.name

        try:
            analysis_report = {
                "pylint_issues": StaticAnalyzer._get_pylint_data(tmp_path),
                "complexity": StaticAnalyzer._get_radon_data(tmp_path)
            }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        return analysis_report

    @staticmethod
    def _get_pylint_data(file_path: str) -> list:
        # We only look for Errors (E) and Warnings (W) to minimize noise
        cmd = ["pylint", "--errors-only", "--output-format=json", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        try:
            data = json.loads(result.stdout)
            return [
                {"line": item['line'], "message": item['message'], "symbol": item['symbol']}
                for item in data
            ]
        except json.JSONDecodeError:
            return []

    @staticmethod
    def _get_radon_data(file_path: str) -> list:
        # Cyclomatic Complexity (cc) - returns blocks with score > 5 (Rank B and below)
        cmd = ["radon", "cc", "-s", "--json", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        try:
            data = json.loads(result.stdout)
            # Radon returns a dict keyed by filename
            file_key = list(data.keys())[0]
            return [
                {"name": item['name'], "complexity": item['complexity'], "rank": item['rank']}
                for item in data[file_key] if item.get('complexity', 0) > 5
            ]
        except (json.JSONDecodeError, IndexError):
            return []