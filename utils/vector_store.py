import os
import re
from chromadb import PersistentClient
from openai import OpenAI

class VectorStore:
    def __init__(self, db_path: str = "./chroma_db"):
        self.client = PersistentClient(path=db_path)
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Using a custom embedding function to keep it LangChain-free
        self.collection = self.client.get_or_create_collection(
            name="repo_context",
            metadata={"hnsw:space": "cosine"}
        )

    def _get_embedding(self, text: str):
        """Direct call to OpenAI for embeddings."""
        text = text.replace("\n", " ")
        return self.openai_client.embeddings.create(
            input=[text], 
            model="text-embedding-3-small"
        ).data[0].embedding

    def _split_code(self, text: str, chunk_size: int = 1000):
        """Naive Python-aware splitter using regex for 'def' and 'class' boundaries."""
        # Split by double newlines or major definitions to keep logic together
        chunks = re.split(r'\n(?=def |class )', text)
        refined_chunks = []
        for chunk in chunks:
            if len(chunk) > chunk_size:
                # Fallback for massive functions: split by lines
                lines = chunk.split('\n')
                for i in range(0, len(lines), 20):
                    refined_chunks.append("\n".join(lines[i:i+20]))
            else:
                refined_chunks.append(chunk)
        return refined_chunks

    def index_repository(self, repo_path: str):
        """Walks repo, chunks code, generates embeddings, and stores in Chroma."""
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        chunks = self._split_code(content)
                        
                        for i, chunk in enumerate(chunks):
                            self.collection.add(
                                documents=[chunk],
                                embeddings=[self._get_embedding(chunk)],
                                metadatas=[{"source": full_path}],
                                ids=[f"{full_path}_{i}"]
                            )

    def query_context(self, code_snippet: str, n_results: int = 2) -> str:
        """Retrieves relevant code chunks."""
        query_emb = self._get_embedding(code_snippet)
        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=n_results
        )
        
        context_blocks = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            context_blocks.append(f"--- Context from {meta['source']} ---\n{doc}")
            
        return "\n\n".join(context_blocks)