"""
core/retrieval.py - Hybrid BM25 + vektorihaku
"""
from typing import List, Tuple
from rank_bm25 import BM25Okapi
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_openai import OpenAIEmbeddings
from core.config import get_settings

settings = get_settings()


class HybridRetriever:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model=settings.embedding_model
        )
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="store_products",
            metadata={"hnsw:space": "cosine"}
        )
        self.bm25_index = None
        self.bm25_documents: List[str] = []
        self.bm25_ids: List[str] = []
        self._rebuild_bm25()

    def _rebuild_bm25(self):
        all_docs = self.collection.get()
        if all_docs["documents"]:
            self.bm25_documents = all_docs["documents"]
            self.bm25_ids = all_docs["ids"]
            tokenized = [doc.lower().split() for doc in self.bm25_documents]
            self.bm25_index = BM25Okapi(tokenized)

    def add_text(self, text: str, source: str = "products") -> int:
        chunks = self._chunk(text)
        if not chunks:
            return 0
        existing = self.collection.count()
        ids = [f"doc_{existing + i}" for i in range(len(chunks))]
        metas = [{"source": source, "chunk": i} for i in range(len(chunks))]
        embeddings = self.embeddings.embed_documents(chunks)
        self.collection.add(documents=chunks, embeddings=embeddings, metadatas=metas, ids=ids)
        self._rebuild_bm25()
        return len(chunks)

    def retrieve(self, query: str, top_k: int = 4) -> List[Tuple[str, dict, float]]:
        if self.collection.count() == 0:
            return []
        query_emb = self.embeddings.embed_query(query)
        vec = self.collection.query(
            query_embeddings=[query_emb],
            n_results=min(top_k * 2, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        vec_rank = {doc_id: r + 1 for r, doc_id in enumerate(vec["ids"][0])}
        bm25_rank = {}
        if self.bm25_index:
            scores = self.bm25_index.get_scores(query.lower().split())
            sorted_ids = sorted(zip(scores, self.bm25_ids), key=lambda x: x[0], reverse=True)
            for r, (_, doc_id) in enumerate(sorted_ids[:top_k * 2]):
                bm25_rank[doc_id] = r + 1
        k = 60
        rrf = {}
        for doc_id in set(vec_rank) | set(bm25_rank):
            score = 0.0
            if doc_id in vec_rank:
                score += 1.0 / (k + vec_rank[doc_id])
            if doc_id in bm25_rank:
                score += 1.0 / (k + bm25_rank[doc_id])
            rrf[doc_id] = score
        top_ids = sorted(rrf, key=lambda x: rrf[x], reverse=True)[:top_k]
        if not top_ids:
            return []
        final = self.collection.get(ids=top_ids, include=["documents", "metadatas"])
        return [(final["documents"][i], final["metadatas"][i], rrf[top_ids[i]]) for i in range(len(top_ids))]

    def get_count(self) -> int:
        return self.collection.count()

    def _chunk(self, text: str, size: int = 500, overlap: int = 80) -> List[str]:
        if not text or len(text) < size:
            return [text] if text else []
        chunks, start = [], 0
        while start < len(text):
            end = start + size
            chunk = text[start:end]
            if end < len(text) and not text[end].isspace():
                last = chunk.rfind(" ")
                if last > size // 2:
                    chunk = chunk[:last]
            if chunk.strip():
                chunks.append(chunk.strip())
            start += size - overlap
        return chunks


_retriever = None


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever
