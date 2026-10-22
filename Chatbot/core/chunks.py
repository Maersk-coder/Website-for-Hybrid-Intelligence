"""
core/chunks.py - cut a paper's text into "chunks" of about 500-700 words.

Chunks are built from whole paragraphs where possible, and each chunk starts with
the last 100 words of the one before (the overlap). The sizes are in settings.py.

Look here when: chunks are much too big or too small (ingest.py --preview shows their sizes).
"""

import re

from settings import CHUNK_MAX_WORDS, CHUNK_MIN_WORDS, OVERLAP_WORDS

# Paragraphs longer than this are cut (between sentences) into smaller pieces.
# Keeping pieces at most (MAX - MIN) words means a chunk can always reach
# CHUNK_MIN_WORDS without going over CHUNK_MAX_WORDS.
PIECE_MAX_WORDS = CHUNK_MAX_WORDS - CHUNK_MIN_WORDS


def split_long_paragraph(text):
    """Cut a paragraph longer than PIECE_MAX_WORDS into pieces, between sentences."""
    # A sentence ends with . ! or ? followed by a space and a capital letter or number.
    # (?<=...) means "right after this" and (?=...) "right before this": the text is split
    # at the space between two sentences, and the full stop stays with its sentence.
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"(\[])", text)

    pieces = []
    current = []
    for sentence in sentences:
        words = sentence.split()
        # A single giant "sentence" (e.g. a table) is cut by word count.
        while len(words) > PIECE_MAX_WORDS:
            if current:
                pieces.append(" ".join(current))
                current = []
            pieces.append(" ".join(words[:PIECE_MAX_WORDS]))
            words = words[PIECE_MAX_WORDS:]
        if len(current) + len(words) > PIECE_MAX_WORDS:
            pieces.append(" ".join(current))
            current = []
        current.extend(words)
    if current:
        pieces.append(" ".join(current))
    return pieces


def make_chunks(paragraphs):
    """Group paragraphs into chunks of CHUNK_MIN_WORDS to CHUNK_MAX_WORDS words, with overlap.

    paragraphs is a list of (page number, text), as made by core/pdf_text.py.
    Returns a list of dictionaries: {"text", "page", "page_end"}.
    "page" is where the chunk's new text starts, "page_end" where it ends.
    """
    # First make sure no single piece is too long.
    pieces = []
    for page, text in paragraphs:
        if len(text.split()) <= PIECE_MAX_WORDS:
            pieces.append((page, text))
        else:
            pieces.extend((page, part) for part in split_long_paragraph(text))

    # How it works: go through the pieces one by one and add them to the chunk being built.
    # When the chunk is full, save it, and start the next one with the end of this one (the overlap).
    chunks = []
    current = []        # the texts in the chunk being built
    current_words = 0
    first_page = None   # page of the first new piece in the chunk
    last_page = None

    # A small function inside this function: it saves the chunk being built.
    # (It can use current, first_page and last_page from the lines above.)
    def close_chunk():
        chunks.append({"text": "\n\n".join(current), "page": first_page, "page_end": last_page})

    for page, text in pieces:
        n_words = len(text.split())

        # Close the chunk when it is big enough and this piece would make it too big.
        if current_words >= CHUNK_MIN_WORDS and current_words + n_words > CHUNK_MAX_WORDS:
            close_chunk()
            # Start the next chunk with the last words of this one (the overlap).
            overlap = " ".join(chunks[-1]["text"].split()[-OVERLAP_WORDS:])
            current = [overlap]
            current_words = len(overlap.split())
            first_page = None

        if first_page is None:
            first_page = page
        last_page = page
        current.append(text)
        current_words += n_words

    # The last chunk (if it has any new text, not only the overlap).
    if first_page is not None:
        close_chunk()

    return chunks
