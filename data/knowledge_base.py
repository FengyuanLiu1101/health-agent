"""Build and load a FAISS vector store from health_facts.txt."""
from __future__ import annotations

import os
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS_PATH = os.path.join(PROJECT_ROOT, "health_facts.txt")
INDEX_DIR = os.path.join(PROJECT_ROOT, "faiss_index")


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


def build_index(force_rebuild: bool = False) -> FAISS:
    """Build the FAISS index from health_facts.txt and save to disk."""
    embeddings = _embeddings()

    if os.path.isdir(INDEX_DIR) and not force_rebuild:
        try:
            return FAISS.load_local(
                INDEX_DIR, embeddings, allow_dangerous_deserialization=True
            )
        except Exception:
            pass

    docs = _load_facts()
    store = FAISS.from_documents(docs, embeddings)
    os.makedirs(INDEX_DIR, exist_ok=True)
    store.save_local(INDEX_DIR)
    return store


def load_or_build_index() -> FAISS:
    """Load existing FAISS index; build it if it does not yet exist."""
    return build_index(force_rebuild=False)


def search(query: str, k: int = 3) -> List[str]:
    store = load_or_build_index()
    results = store.similarity_search(query, k=k)
    return [r.page_content for r in results]


if __name__ == "__main__":
    store = build_index(force_rebuild=True)
    print("Built FAISS index. Sample query: 'how much should I sleep?'")
    for hit in store.similarity_search("how much should I sleep?", k=3):
        print("-", hit.page_content)
