import faiss 
import numpy as np
import json
from pathlib import Path
from typing import List,Dict

class VectorStore:
    """FAISS-based vector store for semantic search."""

    def __init__(self,dim:int=1536):
        """Initialize vector store (1536 for Azure ada-002)."""
        self.dim=dim
        self.index= faiss.IndexFlatL2(dim)
        self.chunks=[]
        self.index_path=Path("data/vector_index")
        self.index_path.mkdir(parents=True, exist_ok=True)
    
    def add(self,embeddings:List[List[float]],chunks:List[Dict]):
        """Add embeddings and chunks to the index."""
        embeddings_array=np.array(embeddings).astype("float32")
        self.index.add(embeddings_array)
        self.chunks.extend(chunks)
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """Search for similar chunks."""
        # Make sure query_embedding is a 1D array, not nested
        if isinstance(query_embedding, list) and len(query_embedding) > 0:
            if isinstance(query_embedding[0], list):
            # If it's nested, flatten it
                query_embedding = query_embedding[0]
    
        query_array = np.array([query_embedding]).astype("float32")
        distances, indices = self.index.search(query_array, k)
    
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.chunks):
                result = self.chunks[idx].copy()
                result["similarity_score"] = float(distance)
                results.append(result)
            
        return results
    
    def save(self,name:str="defaul"):
        """Save index to disk."""
        faiss.write_index(self.index,str(self.index_path / f"{name}.index"))
        with open(self.index_path / f"{name}_chunks.json","w") as f:
            json.dump(self.chunks,f,indent=2)
    
    def load(self,name:str="default"):
        """Load index from disk."""
        index_file=self.index_path / f"{name}.index"
        chunks_file=self.index_path / f"{name}_chunks.json"

        if index_file.exists() and chunks_file.exists():
            self.index=faiss.read_index(str(index_file))
            with open(chunks_file,"r") as f:
                self.chunks=json.load(f)
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get statistics."""
        return {
            "total_vectors": self.index.ntotal,
            "dimension":self.dim,
            "total_chunks":len(self.chunks)
        }


       
