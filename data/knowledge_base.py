"""Build a FAISS vector store from health_facts.txt.

We deliberately do NOT load a pre-built index from disk: FAISS.load_local
unpickles arbitrary Python objects (`allow_dangerous_deserialization=True`),
which is RCE if anything else can write to the index directory. The corpus
is tiny (~30 facts) so re-embedding once per process at startup is fine.
"""
from __future__ import annotations

import os
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS_PATH = os.path.join(PROJECT_ROOT, "health_facts.txt")

_INDEX: FAISS | None = None


def _load_facts() -> List[Document]:
    if not os.path.exists(FACTS_PATH):
        raise FileNotFoundError(f"health_facts.txt not found at {FACTS_PATH}")
    with open(FACTS_PATH, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return [
        Document(page_content=line, metadata={"source": "health_facts.txt", "line": i + 1})
        for i, line in enumerate(lines)
    ]


def _embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model="text-embedding-3-small")


def build_index() -> FAISS:
    """Build the FAISS index in memory from health_facts.txt."""
    docs = _load_facts()
    return FAISS.from_documents(docs, _embeddings())


def load_or_build_index() -> FAISS:
    """Return a process-cached in-memory FAISS index. No disk persistence."""
    global _INDEX
    if _INDEX is None:
        _INDEX = build_index()
    return _INDEX


def search(query: str, k: int = 3) -> List[str]:
    store = load_or_build_index()
    results = store.similarity_search(query, k=k)
    return [r.page_content for r in results]


if __name__ == "__main__":
    store = build_index()
    print("Built FAISS index. Sample query: 'how much should I sleep?'")
    for hit in store.similarity_search("how much should I sleep?", k=3):
        print("-", hit.page_content)
