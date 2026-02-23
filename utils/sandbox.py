import ast

def validate_code_safety(code: str) -> dict:
    """
    Checks if the code is syntactically valid by parsing it into an 
    Abstract Syntax Tree (AST). This is safe because it doesn't execute the code.
    """
    if not code:
        return {"valid": False, "error": "No code provided"}
        
    try:
        ast.parse(code)
        return {"valid": True, "error": None}
    except SyntaxError as e:
        return {
            "valid": False, 
            "error": f"Syntax error on line {e.lineno}: {e.msg}"
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}