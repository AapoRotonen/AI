"""Hybrid BM25 and vector retrieval with deterministic reciprocal-rank fusion."""

from __future__ import annotations

import hashlib
import re
from typing import Iterable, List, Tuple

from rank_bm25 import BM25Okapi
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_openai import OpenAIEmbeddings

from core.config import get_settings

settings = get_settings()


def reciprocal_rank_fusion(
    ranked_lists: Iterable[Iterable[str]], *, k: int = 60
) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranked_ids in ranked_lists:
        for rank, document_id in enumerate(ranked_ids, start=1):
            scores[document_id] = scores.get(document_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


class HybridRetriever:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
        )
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="store_products",
            metadata={"hnsw:space": "cosine"},
        )
        self.bm25_index: BM25Okapi | None = None
        self.bm25_documents: List[str] = []
        self.bm25_ids: List[str] = []
        self._rebuild_bm25()

    def _rebuild_bm25(self) -> None:
        all_docs = self.collection.get()
        self.bm25_documents = all_docs.get("documents") or []
        self.bm25_ids = all_docs.get("ids") or []
        tokenized = [doc.lower().split() for doc in self.bm25_documents]
        self.bm25_index = BM25Okapi(tokenized) if tokenized else None

    def add_text(self, text: str, source: str = "products") -> int:
        documents = self._chunk_with_product_codes(text)
        if not documents:
            return 0
        existing_ids = set(self.collection.get().get("ids") or [])
        ids = [
            hashlib.sha256(f"{source}\0{chunk}".encode("utf-8")).hexdigest()[:24]
            for chunk, _ in documents
        ]
        new_chunks = [
            (doc_id, chunk, product_code)
            for doc_id, (chunk, product_code) in zip(ids, documents)
            if doc_id not in existing_ids
        ]
        if not new_chunks:
            return 0
        new_ids = [item[0] for item in new_chunks]
        new_documents = [item[1] for item in new_chunks]
        metas = [
            {
                "source": source,
                "product_code": product_code or "",
                "chunk": index,
            }
            for index, (_, _, product_code) in enumerate(new_chunks)
        ]
        embeddings = self.embeddings.embed_documents(new_documents)
        self.collection.add(
            documents=new_documents,
            embeddings=embeddings,
            metadatas=metas,
            ids=new_ids,
        )
        self._rebuild_bm25()
        return len(new_documents)

    def retrieve(self, query: str, top_k: int = 4) -> List[Tuple[str, dict, float]]:
        """Return hybrid vector + BM25 results, fused with RRF."""
        return self.retrieve_for_evaluation(query, top_k=top_k, method="hybrid")

    def retrieve_for_evaluation(
        self, query: str, top_k: int = 4, method: str = "hybrid"
    ) -> List[Tuple[str, dict, float]]:
        if method not in {"vector", "bm25", "hybrid"}:
            raise ValueError("method must be vector, bm25, or hybrid")
        count = self.collection.count()
        if count == 0 or top_k <= 0:
            return []

        candidate_count = min(top_k * 2, count)
        vector_ids = self._vector_ids(query, candidate_count) if method in {"vector", "hybrid"} else []
        bm25_ids = self._bm25_ranked_ids(query, candidate_count) if method in {"bm25", "hybrid"} else []
        if method == "vector":
            ranked_ids = vector_ids[:top_k]
            scores = {doc_id: 1.0 / rank for rank, doc_id in enumerate(vector_ids, start=1)}
        elif method == "bm25":
            ranked_ids = bm25_ids[:top_k]
            scores = {doc_id: 1.0 / rank for rank, doc_id in enumerate(bm25_ids, start=1)}
        else:
            fused = reciprocal_rank_fusion((vector_ids, bm25_ids))
            ranked_ids = [doc_id for doc_id, _ in fused[:top_k]]
            scores = dict(fused)
        return self._fetch_ranked(ranked_ids, scores)

    def _vector_ids(self, query: str, limit: int) -> list[str]:
        query_embedding = self.embeddings.embed_query(query)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )
        return result.get("ids", [[]])[0]

    def _bm25_ranked_ids(self, query: str, limit: int) -> list[str]:
        if self.bm25_index is None:
            return []
        scores = self.bm25_index.get_scores(query.lower().split())
        ranked = sorted(
            zip(scores, self.bm25_ids),
            key=lambda item: (-float(item[0]), item[1]),
        )
        return [doc_id for _, doc_id in ranked[:limit]]

    def _fetch_ranked(self, ids: list[str], scores: dict[str, float]) -> List[Tuple[str, dict, float]]:
        if not ids:
            return []
        docs = self.collection.get(ids=ids, include=["documents", "metadatas"])
        by_id = {
            document_id: (document, metadata or {})
            for document_id, document, metadata in zip(
                docs.get("ids", []), docs.get("documents", []), docs.get("metadatas", [])
            )
        }
        results = []
        for document_id in ids:
            item = by_id.get(document_id)
            if item is None:
                continue
            document, metadata = item
            metadata = dict(metadata)
            metadata["document_id"] = document_id
            metadata.setdefault("product_code", self._product_code(document) or "")
            results.append((document, metadata, float(scores.get(document_id, 0.0))))
        return results

    def get_count(self) -> int:
        return self.collection.count()

    @staticmethod
    def _product_code(text: str) -> str | None:
        match = re.search(r"Tuotekoodi\s*:\s*([A-Z]{3}-\d{3})", text, re.IGNORECASE)
        return match.group(1).upper() if match else None

    @classmethod
    def _chunk_with_product_codes(cls, text: str) -> list[tuple[str, str | None]]:
        sections = re.split(r"(?=^TUOTE\s+\d+\s*:)", text, flags=re.IGNORECASE | re.MULTILINE)
        output = []
        for section in sections:
            product_code = cls._product_code(section)
            output.extend((chunk, product_code) for chunk in cls._chunk(section))
        return output

    @staticmethod
    def _chunk(text: str, size: int = 500, overlap: int = 80) -> List[str]:
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
