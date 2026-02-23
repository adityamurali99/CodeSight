import os
import re
from chromadb import PersistentClient
from openai import OpenAI

class VectorStore:
    def __init__(self, db_path: str = "./chroma_db"):
        self.client = PersistentClient(path=db_path)
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.collection = self.client.get_or_create_collection(
            name="repo_context",
            metadata={"hnsw:space": "cosine"}
        )

    def _get_batch_embeddings(self, texts: list):
        """Optimized: Sends multiple chunks in one API call."""
        cleaned_texts = [t.replace("\n", " ") for t in texts]
        response = self.openai_client.embeddings.create(
            input=cleaned_texts, 
            model="text-embedding-3-small"
        )
        return [item.embedding for item in response.data]

    def _split_code(self, text: str, chunk_size: int = 1000):
        chunks = re.split(r'\n(?=def |class )', text)
        return [c for c in chunks if c.strip()]

    def index_repository(self, repo_path: str):
        """Walks repo and uses batch processing to store embeddings."""
        documents, embeddings, metadatas, ids = [], [], [], []
        
        for root, _, files in os.walk(repo_path):
            if ".git" in root or "__pycache__" in root: continue
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8") as f:
                        chunks = self._split_code(f.read())
                        if not chunks: continue
                        
                        # Batch get embeddings for all chunks in this file
                        file_embeddings = self._get_batch_embeddings(chunks)
                        
                        for i, (chunk, emb) in enumerate(zip(chunks, file_embeddings)):
                            documents.append(chunk)
                            embeddings.append(emb)
                            metadatas.append({"source": file})
                            ids.append(f"{file}_{i}")

        if documents:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

    def query_context(self, code_snippet: str, n_results: int = 2) -> str:
        query_emb = self._get_batch_embeddings([code_snippet])[0]
        results = self.collection.query(query_embeddings=[query_emb], n_results=n_results)
        return "\n\n".join([f"Context: {d}" for d in results['documents'][0]])