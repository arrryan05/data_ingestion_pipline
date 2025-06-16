# src/chroma_setup.py

import logging
from chromadb import Client as ChromaClient
from chromadb.config import Settings

_chroma_client = None

def init_chroma(persist_dir: str = ".chromadb", collection_name: str = "documents"):
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    client = ChromaClient(Settings(persist_directory=persist_dir))
    existing = {c.name for c in client.list_collections()}
    if collection_name not in existing:
        client.get_or_create_collection(name=collection_name)
        logging.info(f"🔧 Created ChromaDB collection '{collection_name}'")
    else:
        logging.info(f"⚙️  ChromaDB collection '{collection_name}' already exists")
    _chroma_client = client
    return _chroma_client

def get_chroma_client():
    if _chroma_client is None:
        raise RuntimeError("Chroma client not initialized; call init_chroma() first")
    return _chroma_client
