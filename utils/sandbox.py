import sys
import io
import contextlib

def validate_code_safety(code: str) -> dict:
    """
    Checks if the code is syntactically valid and can be 
    parsed into an AST without execution.
    """
    try:
        compile(code, "<string>", "exec")
        return {"valid": True, "error": None}
    except SyntaxError as e:
        return {"valid": False, "error": f"SyntaxError on line {e.lineno}: {e.msg}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}

def test_execution(code: str):
    """
    Optional: Extremely basic execution check. 
    Warning: Do not run untrusted code in a production environment 
    without heavy containerization (Docker/gVisor).
    """
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            # We use a limited global dict to prevent some obvious malicious acts
            exec(code, {"__builtins__": __builtins__}, {})
        return {"success": True, "output": output.getvalue(), "error": None}
    except Exception as e:
        return {"success": False, "output": output.getvalue(), "error": str(e)}