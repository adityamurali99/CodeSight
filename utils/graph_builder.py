import ast

class CodeGraph:
    def __init__(self):
        self.nodes = {}  # name -> {"source": str, "code": str, "type": str}
        self.edges = {}  # name -> set(callee_names)

class GraphBuilder(ast.NodeVisitor):
    def __init__(self, source_path: str):
        self.source_path = source_path
        self.current_scope = None
        self.graph = CodeGraph()

    def visit_ClassDef(self, node: ast.ClassDef):
        name = node.name
        # Track inheritance as edges
        bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
        self.graph.nodes[name] = {
            "source": self.source_path, 
            "code": ast.unparse(node), 
            "type": "class"
        }
        self.graph.edges.setdefault(name, set()).update(bases)
        
        old_scope = self.current_scope
        self.current_scope = name
        self.generic_visit(node)
        self.current_scope = old_scope

    def visit_FunctionDef(self, node: ast.FunctionDef):
        full_name = f"{self.current_scope}.{node.name}" if self.current_scope else node.name
        self.graph.nodes[full_name] = {
            "source": self.source_path, 
            "code": ast.unparse(node), 
            "type": "function"
        }
        
        old_scope = self.current_scope
        self.current_scope = full_name
        self.generic_visit(node)
        self.current_scope = old_scope

    def visit_Call(self, node: ast.Call):
        callee = None
        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr
            
        if callee and self.current_scope:
            self.graph.edges.setdefault(self.current_scope, set()).add(callee)
        self.generic_visit(node)