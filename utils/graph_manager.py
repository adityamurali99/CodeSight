import ast
import logging
from .graph_builder import GraphBuilder

logger = logging.getLogger("graph-manager")

class GraphManager:
    def __init__(self):
        self.nodes = {}
        self.edges = {}          # Outgoing: What this node calls
        self.reverse_edges = {}  # Incoming: What calls this node

    def build_from_contents(self, repo_contents: list):
        """Builds a deterministic map from GitHub file list."""
        self.nodes.clear()
        self.edges.clear()
        self.reverse_edges.clear()

        for file_data in repo_contents:
            try:
                tree = ast.parse(file_data["content"])
                visitor = GraphBuilder(file_data["path"])
                visitor.visit(tree)
                
                self.nodes.update(visitor.graph.nodes)
                for caller, callees in visitor.graph.edges.items():
                    self.edges.setdefault(caller, set()).update(callees)
                    for callee in callees:
                        self.reverse_edges.setdefault(callee, set()).add(caller)
            except Exception as e:
                logger.error(f"Error parsing {file_data['path']}: {e}")

    def get_context(self, code_snippet: str, hops: int = 2) -> str:
        """Forward RAG: Finds what the snippet calls."""
        targets = self._get_defined_names(code_snippet)
        return self._walk(targets, self.edges, hops, "DEPENDENCY")

    def get_impact_analysis(self, code_snippet: str, hops: int = 1) -> str:
        """Reverse RAG: Finds what calls this code."""
        targets = self._get_defined_names(code_snippet)
        return self._walk(targets, self.reverse_edges, hops, "IMPACTED NODE")

    def _get_defined_names(self, snippet):
        try:
            tree = ast.parse(snippet)
            return [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        except: return []

    def _walk(self, start_nodes, edge_map, max_hops, label):
        context, visited = [], set()
        queue = [(t, 0) for t in start_nodes if t in self.nodes or t in edge_map]

        while queue:
            name, dist = queue.pop(0)
            if name in visited or dist > max_hops: continue
            visited.add(name)

            node = self.nodes.get(name)
            if node:
                context.append(f"--- {label}: {name} ({node['source']}) ---\n{node['code']}")
            
            for neighbor in edge_map.get(name, []):
                queue.append((neighbor, dist + 1))
        return "\n\n".join(context)