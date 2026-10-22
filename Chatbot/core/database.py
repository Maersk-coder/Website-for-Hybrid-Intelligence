"""
core/database.py - the search index (ChromaDB): store chunks, and find the ones that match a question.

ChromaDB turns each chunk into an "embedding" (a list of numbers that captures
what the text is about). A question gets an embedding too, and the chunks whose
numbers are closest to the question's are the best matches.

Look here when: the search finds the wrong excerpts (check with  python ask.py --show-chunks).
"""

import chromadb
from chromadb.config import Settings

from core.errors import ChatbotError
from settings import COLLECTION_NAME, DATABASE_FOLDER, NUMBER_OF_CHUNKS


def open_database():
    """Open (or create) the ChromaDB database in data/chroma/."""
    DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)
    # anonymized_telemetry=False: don't send usage statistics to ChromaDB's makers.
    return chromadb.PersistentClient(
        path=str(DATABASE_FOLDER),
        settings=Settings(anonymized_telemetry=False),
    )


# ---------------------------------------------------------------------------
# Searching
# ---------------------------------------------------------------------------

_collection = None  # the index is opened once, then reused


def get_collection():
    """Open the index for searching (only the first time) and return it."""
    # "global" lets this function change _collection (outside the function), so the opened
    # index is kept for the next question instead of being opened again every time.
    global _collection
    if _collection is None:
        collection = open_database().get_or_create_collection(name=COLLECTION_NAME)
        if collection.count() == 0:
            raise ChatbotError("The index is empty. Run: python ingest.py")
        _collection = collection
    return _collection


def page_label(chunk):
    """'3' for a chunk on one page, '3-4' for a chunk that runs over two pages."""
    if chunk["page"] == chunk["page_end"]:
        return str(chunk["page"])
    return f"{chunk['page']}-{chunk['page_end']}"


def retrieve(question, number=NUMBER_OF_CHUNKS):
    """Return the chunks that are closest in meaning to the question.

    Each chunk is a dictionary with: text, title, file_name, page, page_end, distance.
    "distance" says how far the chunk is from the question: lower = better match.
    """
    result = get_collection().query(query_texts=[question], n_results=number)

    chunks = []
    # Chroma returns lists inside lists (one list per question). We asked one question, so [0].
    for text, info, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        chunks.append({
            "text": text,
            "title": info["title"],
            "file_name": info["file_name"],
            "page": info["page"],
            "page_end": info["page_end"],
            "distance": distance,
        })
    return chunks
