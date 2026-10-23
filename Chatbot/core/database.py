"""
core/database.py - the search index (ChromaDB): store chunks, and find the ones that match a question.

Each chunk is stored with its "embedding" (a list of numbers that captures what the text is
about, made by core/embeddings.py). A question gets an embedding too, and the chunks whose
numbers are closest to the question's are the best matches.

Look here when: the search finds the wrong excerpts (check with  python ask.py --show-chunks).
"""

import chromadb
from chromadb.config import Settings

from core.embeddings import embed_question
from core.errors import ChatbotError
from settings import (
    COLLECTION_NAME, DATABASE_FOLDER, EMBEDDING_MODEL, MAX_CHUNKS_PER_PAPER, NUMBER_OF_CHUNKS, SEARCH_CANDIDATES,
)


def open_database():
    """Open (or create) the ChromaDB database in data/chroma/."""
    DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)
    # anonymized_telemetry=False: don't send usage statistics to ChromaDB's makers.
    return chromadb.PersistentClient(
        path=str(DATABASE_FOLDER),
        settings=Settings(anonymized_telemetry=False),
    )


def open_collection(client):
    """Open (or create) the collection that holds the chunks.

    embedding_function=None: we make the embeddings ourselves (core/embeddings.py), so ChromaDB
    must not use its own model. The collection remembers which model made its embeddings
    ("embedding_model"), so a mix-up can be noticed (see index_matches_model).
    """
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=None,
        metadata={"embedding_model": EMBEDDING_MODEL},
    )


def index_matches_model(collection):
    """True if the index was built with EMBEDDING_MODEL (or is still empty).

    Numbers from two different embedding models can't be compared: a question embedded by one
    model would find nonsense among chunks embedded by another. Then the index must be rebuilt.
    """
    return collection.count() == 0 or (collection.metadata or {}).get("embedding_model") == EMBEDDING_MODEL


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
        collection = open_collection(open_database())
        if collection.count() == 0:
            raise ChatbotError("The index is empty. Run: python ingest.py")
        if not index_matches_model(collection):
            raise ChatbotError(f"The index was built with another embedding model than {EMBEDDING_MODEL}. "
                               "Run: python ingest.py --rebuild")
        _collection = collection
    return _collection


def page_label(chunk):
    """'3' for a chunk on one page, '3-4' for a chunk that runs over two pages."""
    if chunk["page"] == chunk["page_end"]:
        return str(chunk["page"])
    return f"{chunk['page']}-{chunk['page_end']}"


def retrieve(question, number=NUMBER_OF_CHUNKS, avoid=None):
    """Return the chunks that are closest in meaning to the question.

    At most MAX_CHUNKS_PER_PAPER of them come from the same paper (see settings.py).
    avoid (optional): chunks to use only if there aren't enough others, as a set of
    (paper title in small letters, page label) pairs, e.g. {("hybrid intelligence", "4-5")}.
    Used for follow-up questions, so the AI gets new material instead of what it already used.
    Each chunk is a dictionary with: text, title, file_name, page, page_end, distance.
    "distance" says how far the chunk is from the question: lower = better match.
    """
    collection = get_collection()
    # Ask for more than we need (but not more than the index has), so there's enough to choose from.
    candidates = min(max(SEARCH_CANDIDATES, number), collection.count())
    result = collection.query(query_embeddings=[embed_question(question)], n_results=candidates)

    found = []
    # Chroma returns lists inside lists (one list per question). We asked one question, so [0].
    for text, info, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        found.append({
            "text": text,
            "title": info["title"],
            "file_name": info["file_name"],
            "page": info["page"],
            "page_end": info["page_end"],
            "distance": distance,
        })

    # Go down the list, best match first, and skip a chunk if its paper already has its maximum,
    # or if it is one to avoid.
    avoid = avoid or set()
    chosen = []
    per_paper = {}   # file name -> how many of its chunks are chosen so far
    for chunk in found:
        if (chunk["title"].lower(), page_label(chunk)) in avoid:
            continue
        if per_paper.get(chunk["file_name"], 0) < MAX_CHUNKS_PER_PAPER:
            chosen.append(chunk)
            per_paper[chunk["file_name"]] = per_paper.get(chunk["file_name"], 0) + 1
        if len(chosen) == number:
            return chosen

    # Not enough different papers among the candidates (e.g. only 1 or 2 papers in the index), or
    # too many to avoid: then fill up with the best of the skipped ones after all.
    chosen += [chunk for chunk in found if chunk not in chosen][: number - len(chosen)]
    return sorted(chosen, key=lambda chunk: chunk["distance"])
