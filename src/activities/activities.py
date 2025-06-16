import os
import tempfile
from typing import List, Tuple, Dict, Any
from temporalio import activity

def _suffix_from_url(url: str) -> str:
    from urllib.parse import urlparse
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext in {".pdf", ".docx", ".doc", ".xls", ".xlsx"}:
        return ext
    return ""

@activity.defn
async def fetch_document(file_url: str) -> bytes:
    # Deferred import
    import aiohttp  

    timeout = aiohttp.ClientTimeout(total=300)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(file_url) as resp:
            resp.raise_for_status()
            data = await resp.read()
            activity.logger.info(f"Fetched {len(data)} bytes from {file_url}")
            return data

@activity.defn
async def parse_document(document_bytes: bytes, file_url: str) -> List[Tuple[int, str]]:
    """
    DIY parser: uses pypdf for PDF, python-docx for .docx, textract for .doc,
    pandas for .xls/.xlsx. Returns list of (chunk_index, text).
    """
    suffix = _suffix_from_url(file_url)
    tmp_suffix = suffix or ".bin"
    # Write to a temp file so libraries can read from disk
    with tempfile.NamedTemporaryFile(delete=False, suffix=tmp_suffix) as tmp:
        tmp.write(document_bytes)
        tmp_path = tmp.name

    try:
        # Extract raw text based on extension
        if suffix == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(tmp_path)
            text = "".join(page.extract_text() or "" for page in reader.pages)

        elif suffix == ".docx":
            import docx
            doc = docx.Document(tmp_path)
            text = "\n".join(p.text for p in doc.paragraphs)

        elif suffix == ".doc":
            # textract will shell out to antiword or similar
            import textract
            text = textract.process(tmp_path).decode("utf-8")

        elif suffix in {".xlsx", ".xls"}:
            import pandas as pd
            import io
            buf = io.BytesIO(document_bytes)
            sheets = pd.read_excel(buf, sheet_name=None)  # dict of DataFrames
            lines: List[str] = []
            for name, df in sheets.items():
                lines.append(f"--- Sheet: {name} ---")
                # each row → one line
                for row in df.fillna("").values:
                    joined = " | ".join(str(cell) for cell in row if str(cell).strip())
                    if joined:
                        lines.append(joined)
            text = "\n".join(lines)

        else:
            raise activity.ApplicationError(f"Unsupported file extension: {suffix}")

        # Split into paragraphs
        paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
        activity.logger.info(f"Extracted {len(paragraphs)} paragraphs from {suffix or 'unknown'} file")

        # Chunk into ~500-word segments
        chunks: List[Tuple[int, str]] = []
        current_words: List[str] = []
        word_count = 0
        idx = 0

        for para in paragraphs:
            words = para.split()
            if word_count + len(words) > 500 and current_words:
                chunks.append((idx, " ".join(current_words)))
                idx += 1
                current_words = []
                word_count = 0
            current_words.extend(words)
            word_count += len(words)

        if current_words:
            chunks.append((idx, " ".join(current_words)))

        activity.logger.info(f"Created {len(chunks)} text chunks from {suffix or 'unknown'} file")
        return chunks

    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

@activity.defn
async def generate_embedding(text: str) -> List[float]:
    """
    Generating a Cohere embedding for the given chunk of text.
    """
    import asyncio
    import cohere
    import random

    api_key = os.environ["COHERE_API_KEY"]
    client = cohere.Client(api_key)

    for attempt in range(3):
        try:
            response = client.embed(
                texts=[text],
                model="embed-english-v3.0",
                input_type="search_document",
            )
            emb = response.embeddings[0]
            activity.logger.info(f"Generated embedding (dim {len(emb)})")
            return emb
        except Exception as e:
            activity.logger.warning(f"Embed attempt {attempt+1}/3 failed: {e}")
            if attempt == 2:
                raise
            await asyncio.sleep((2 ** attempt) + random.random())


@activity.defn
async def store_chunk(record: Dict[str, Any]) -> None:
    """
    Storing the chunk into the in‐process ChromaDB 'documents' collection.
    """
    from chroma_client import get_chroma_client  
    
    client = get_chroma_client()

    coll = client.get_collection("documents")
    chunk_id = f"{record['file_id']}::{record['chunk_index']}"
    coll.add(
        ids=[chunk_id],
        embeddings=[record["embedding"]],
        metadatas=[{"file_id": record["file_id"], "chunk_index": record["chunk_index"]}],
        documents=[record["text"]],
    )
    activity.logger.info(f"Stored chunk {chunk_id} in ChromaDB")