"""
core/database.py - the search index (ChromaDB): store chunks, and find the ones that match a question.

Two searches work together:
  - the MEANING search: each chunk is stored with its "embedding" (a list of numbers that
    captures what the text is about, made by core/embeddings.py). A question gets an embedding
    too, and the chunks whose numbers are closest to the question's are the best matches.
  - the WORD search (core/keywords.py): chunks that contain the question's rare words.
Their two rankings are combined, so a chunk that does well in either one moves up.

Look here when: the search finds the wrong excerpts (check with  python ask.py --show-chunks).
"""

import chromadb
import numpy as np
from chromadb.config import Settings

from core.embeddings import embed_question
from core.errors import ChatbotError
from core.keywords import WordIndex
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


_word_index = None  # the word search's counts, made once (from the chunks in the index), then reused


def get_word_index():
    """The word search (core/keywords.py) for the chunks in the index.

    Made the first time it's needed. After adding papers with ingest.py, restart api.py
    so it's made again with the new chunks.
    """
    global _word_index
    if _word_index is None:
        _word_index = WordIndex(get_collection())
    return _word_index


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
    question_numbers = embed_question(question)
    # Ask for more than we need (but not more than the index has), so there's enough to choose from.
    size = min(max(SEARCH_CANDIDATES, number), collection.count())

    def make_chunk(chunk_id, text, info, distance):
        return {"id": chunk_id, "text": text, "title": info["title"], "file_name": info["file_name"],
                "page": info["page"], "page_end": info["page_end"], "distance": distance}

    def search(exclude_papers=()):
        """The best-matching chunks by MEANING, best first (optionally leaving out some papers)."""
        where = {"file_name": {"$nin": list(exclude_papers)}} if exclude_papers else None
        result = collection.query(query_embeddings=[question_numbers], n_results=size, where=where)
        # Chroma returns lists inside lists (one list per question). We asked one question, so [0].
        return [make_chunk(*row) for row in zip(
            result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0])]

    def search_both():
        """The best-matching chunks by MEANING and by WORDS together, best first.

        The two rankings are combined with "reciprocal rank fusion": a chunk scores 1/(60 + its place)
        in each ranking it appears in, and the scores are added up. So a chunk near the top of
        either ranking moves up, and one near the top of both moves up most.
        """
        by_meaning = search()
        by_words = get_word_index().search(question, size)

        # Chunks found only by the word search: fetch their text, and work out their distance
        # (so every chunk has one, for the off-topic check and --show-chunks).
        missing = [chunk_id for chunk_id in by_words if chunk_id not in {c["id"] for c in by_meaning}]
        extra = []
        if missing:
            got = collection.get(ids=missing, include=["documents", "metadatas", "embeddings"])
            for chunk_id, text, info, numbers in zip(got["ids"], got["documents"], got["metadatas"], got["embeddings"]):
                # The same distance ChromaDB uses: the sum of the squared differences of the numbers.
                distance = float(np.sum((np.array(numbers) - np.array(question_numbers)) ** 2))
                extra.append(make_chunk(chunk_id, text, info, distance))

        score = {}
        for place, chunk in enumerate(by_meaning):
            score[chunk["id"]] = score.get(chunk["id"], 0) + 1 / (60 + place)
        for place, chunk_id in enumerate(by_words):
            score[chunk_id] = score.get(chunk_id, 0) + 1 / (60 + place)
        return sorted(by_meaning + extra, key=lambda chunk: score[chunk["id"]], reverse=True)

    avoid = avoid or set()
    chosen = []
    per_paper = {}   # file name -> how many of its chunks are chosen so far
    skipped = []     # chunks left out (paper full, or to avoid), in case we need them after all

    def choose_from(found):
        """Go down the list, best match first, and take a chunk unless its paper already has its
        maximum, it's one to avoid, or it's already chosen."""
        for chunk in found:
            if len(chosen) == number:
                return
            if any(chunk["id"] == c["id"] for c in chosen + skipped):
                continue
            if (chunk["title"].lower(), page_label(chunk)) in avoid \
                    or per_paper.get(chunk["file_name"], 0) >= MAX_CHUNKS_PER_PAPER:
                skipped.append(chunk)
                continue
            chosen.append(chunk)
            per_paper[chunk["file_name"]] = per_paper.get(chunk["file_name"], 0) + 1

    choose_from(search_both())

    # Not enough yet, because some papers filled all the best places? Then search again in the
    # OTHER papers only, so the AI also sees what they say (other points of view).
    full_papers = [name for name, count in per_paper.items() if count >= MAX_CHUNKS_PER_PAPER]
    if len(chosen) < number and full_papers:
        choose_from(search(exclude_papers=full_papers))

    # Still not enough (e.g. only 1 or 2 papers in the index, or many to avoid):
    # then fill up with the best of the skipped ones after all.
    skipped.sort(key=lambda chunk: chunk["distance"])
    chosen += skipped[: number - len(chosen)]
    return sorted(chosen, key=lambda chunk: chunk["distance"])
