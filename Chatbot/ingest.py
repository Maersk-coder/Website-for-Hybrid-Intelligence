"""
ingest.py - builds the search index from the research papers.

What it does, step by step:
  1. Opens every PDF in the papers/ folder.
  2. Takes the text out page by page and cleans it
     (removes headers, footers, page numbers and the reference list).
  3. Finds the paper's title.
  4. Cuts the text into "chunks" of about 300-500 words.
  5. Saves the chunks in ChromaDB, a small database stored in data/chroma/.
     ChromaDB turns each chunk into an "embedding" (a list of numbers that
     captures what the text is about), so later we can find the chunks
     that best match a question.

How to run it (inside the Chatbot folder, with the virtual environment on):
  python ingest.py                       add new PDFs to the index
  python ingest.py --rebuild             delete the index and build it again
  python ingest.py --preview FILE.pdf    save the cleaned text of one PDF in preview.txt
                                         (nothing is added to the index)
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import chromadb
import pymupdf  # PyMuPDF: reads PDF files
from chromadb.config import Settings


# ---------------------------------------------------------------------------
# Settings (change these if you want)
# ---------------------------------------------------------------------------

# Folders. They are found from where this file is, so the script works
# no matter which folder you run it from.
HERE = Path(__file__).parent
PAPERS_FOLDER = HERE / "papers"
DATABASE_FOLDER = HERE / "data" / "chroma"
PREVIEW_FILE = HERE / "preview.txt"   # where --preview saves the cleaned text

# The name of the "collection" (like a table) in ChromaDB that holds the chunks.
COLLECTION_NAME = "papers"

# Chunk sizes, counted in words.
CHUNK_MIN_WORDS = 500   # a chunk is not closed before it has this many words
CHUNK_MAX_WORDS = 700   # ...and never grows past this many
OVERLAP_WORDS = 100      # each chunk starts with the last 50 words of the one before,
                        # so a sentence cut at the edge is still found whole

# Paragraphs longer than this are cut (between sentences) into smaller pieces.
# Keeping pieces at most (MAX - MIN) words means a chunk can always reach
# 300 words without going over 500.
PIECE_MAX_WORDS = CHUNK_MAX_WORDS - CHUNK_MIN_WORDS

# Headers and footers are looked for in the top and bottom 10% of each page.
MARGIN_SHARE = 0.10

# A text counts as a repeated header/footer if it is on at least 30% of the pages.
REPEAT_SHARE = 0.30

# A PDF with fewer words than this per page is probably a scanned image.
LOW_TEXT_WORDS_PER_PAGE = 50


# ---------------------------------------------------------------------------
# Patterns used for cleaning (regular expressions)
# ---------------------------------------------------------------------------

# A line that is only a page number: "7", "Page 7", "7 of 20", "7/20"
PAGE_NUMBER = re.compile(r"^(page\s*)?\d{1,4}(\s*(of|/)\s*\d{1,4})?$", re.IGNORECASE)

# The heading that starts the reference list, e.g. "References", "7. References",
# "VII. REFERENCES", "Bibliography".
REFERENCES_HEADING = re.compile(
    r"^\s*(\d+\.?|[IVXLC]+\.)?\s*"
    r"(references|bibliography|works cited|literature cited|reference list)\s*:?\s*$",
    re.IGNORECASE,
)

# The heading where the paper itself starts, after the title and author names:
# "Abstract", "Abstract.", "1 Introduction", "1. Introduction", "I. INTRODUCTION"
START_HEADING = re.compile(r"^\s*(abstract\b|(\d+\.?|I\.)?\s*introduction\s*$)", re.IGNORECASE)

# The stamp arXiv prints down the side of page 1: "arXiv:2101.12345v2 [cs.AI] 12 Jan 2021"
ARXIV_STAMP = re.compile(r"^arXiv:\d{4}\.\d{4,5}", re.IGNORECASE)

# Special "joined letter" characters some PDFs use, swapped for normal letters.
LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}


# ---------------------------------------------------------------------------
# Step 1-2: read and clean the text of one PDF
# ---------------------------------------------------------------------------

def clean_block(text):
    """Clean one block of text (roughly one paragraph) taken from a PDF."""
    for joined, plain in LIGATURES.items():
        text = text.replace(joined, plain)

    # A "soft hyphen" is an invisible hyphen used for line breaks. Remove it.
    text = text.replace("­\n", "").replace("­", "")

    # Join words broken over two lines: "collab-\noration" -> "collaboration".
    # Only when the next line starts with a small letter...
    text = re.sub(r"(\w)-[ \t]*\n[ \t]*([a-z])", r"\1\2", text)
    # ...otherwise keep the hyphen: "Human-\nAI" -> "Human-AI".
    text = re.sub(r"(\w)-[ \t]*\n[ \t]*", r"\1-", text)

    # Any other line breaks inside a paragraph become normal spaces.
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fingerprint(text):
    """A simplified version of a text, used to spot headers/footers that repeat.

    Numbers are replaced with '#', so "Journal of AI, page 3" and
    "Journal of AI, page 4" count as the same footer.
    """
    return re.sub(r"\d+", "#", text.lower()).strip()


def is_real_title(title):
    """Check whether a title from the PDF's hidden information looks real.

    PDF files often carry a useless title such as "Microsoft Word - draft3.docx".
    """
    if not title:
        return False
    title = title.strip()
    lower = title.lower()
    if len(title) < 10 or " " not in title:
        return False
    bad_signs = ("untitled", "microsoft word", ".doc", ".pdf", ".tex", ".dvi")
    if any(sign in lower for sign in bad_signs):
        return False
    if lower.startswith(("arxiv", "doi")):
        return False
    return True


def title_from_first_page(doc):
    """Guess the title as the text in the biggest letters near the top of page 1."""
    page = doc[0]
    pieces = []  # (letter size, text) for every bit of text near the top
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            # Skip sideways text (like the arXiv stamp down the edge).
            if abs(line["dir"][0]) < 0.99:
                continue
            for span in line["spans"]:
                text = span["text"].strip()
                near_top = span["bbox"][1] < page.rect.height * 0.6
                if len(text) >= 2 and near_top and not ARXIV_STAMP.match(text):
                    pieces.append((span["size"], text))

    if not pieces:
        return None

    biggest = max(size for size, _ in pieces)
    title = " ".join(text for size, text in pieces if size >= biggest - 0.5)
    title = re.sub(r"\s+", " ", title).strip()

    # Very short or very long "titles" are probably something else.
    if 10 <= len(title) <= 250:
        return title
    return None


def find_title(doc, pdf_path):
    """Return (title, where it came from). Tries three places, best first."""
    metadata_title = (doc.metadata or {}).get("title", "")
    if is_real_title(metadata_title):
        return metadata_title.strip(), "PDF metadata"

    page_title = title_from_first_page(doc)
    if page_title:
        return page_title, "first page"

    # Last option: the file name, "my_paper-2021.pdf" -> "my paper 2021"
    return re.sub(r"[_\-]+", " ", pdf_path.stem).strip(), "file name"


def find_start(pages):
    """Find where the paper itself starts, after the title, authors and addresses.

    Looks for an "Abstract" or "Introduction" heading on the first 3 pages.
    Returns (page index, block index) of that heading, or None if there is none
    (then nothing is skipped).
    """
    for page_index, blocks in enumerate(pages[:3]):
        for block_index, block in enumerate(blocks):
            first_line = block["raw"].strip().split("\n")[0]
            if START_HEADING.match(first_line):
                return page_index, block_index
    return None


def extract_paper(pdf_path):
    """Read one PDF and return its cleaned text plus some information about it.

    The result is a dictionary with:
      title, title_source  - the paper title and where it was found
      num_pages            - number of pages in the PDF
      paragraphs           - list of (page number, paragraph text)
      removed              - examples of headers/footers that were removed
      start                - (page, heading) where the text starts, or None
      references_page      - page where the reference list starts (or None)
      word_count           - number of words kept
    """
    doc = pymupdf.open(pdf_path)
    num_pages = len(doc)
    title, title_source = find_title(doc, pdf_path)

    # --- Read every page as a list of blocks -------------------------------
    # A "block" is a group of lines PyMuPDF thinks belong together,
    # usually one paragraph, heading or caption.
    pages = []
    for page in doc:
        height = page.rect.height
        blocks = []
        for x0, y0, x1, y1, text, block_no, block_type in page.get_text("blocks"):
            if block_type != 0:  # 0 = text, 1 = image
                continue
            in_margin = y1 < height * MARGIN_SHARE or y0 > height * (1 - MARGIN_SHARE)
            blocks.append({"raw": text, "text": clean_block(text), "in_margin": in_margin})
        pages.append(blocks)
    doc.close()

    # --- Find headers/footers: text in the margins that repeats on many pages ---
    margin_counts = Counter()
    for blocks in pages:
        # set(): count each text once per page
        margin_counts.update({fingerprint(b["text"]) for b in blocks if b["in_margin"]})
    min_repeats = max(3, int(num_pages * REPEAT_SHARE))
    repeated = {fp for fp, count in margin_counts.items() if count >= min_repeats}

    # --- Skip the title page part (title, authors, addresses, dates) --------
    # The title is stored separately, so nothing useful is lost.
    start = find_start(pages)

    # --- Keep the good blocks, stop at the reference list -------------------
    paragraphs = []
    removed = set()
    references_page = None

    for page_index, blocks in enumerate(pages):
        page_number = page_index + 1
        for block_index, block in enumerate(blocks):
            text = block["text"]
            if len(text) < 2:
                continue
            if start and (page_index, block_index) < start:
                continue  # before the Abstract/Introduction heading

            # The reference list: only trusted in the later part of the paper,
            # so a "References" mentioned early on doesn't cut the paper short.
            first_line = block["raw"].strip().split("\n")[0]
            if REFERENCES_HEADING.match(first_line) and page_index >= int(num_pages * 0.4):
                references_page = page_number
                break

            if block["in_margin"] and fingerprint(text) in repeated:
                removed.add(text)
                continue
            if PAGE_NUMBER.match(text):
                continue
            if ARXIV_STAMP.match(text):
                removed.add(text)
                continue

            paragraphs.append((page_number, text))

        if references_page:
            break  # everything after the reference heading is skipped

    word_count = sum(len(text.split()) for _, text in paragraphs)
    return {
        "title": title,
        "title_source": title_source,
        "num_pages": num_pages,
        "paragraphs": paragraphs,
        "removed": sorted(removed),
        "start": (start[0] + 1, pages[start[0]][start[1]]["text"][:40]) if start else None,
        "references_page": references_page,
        "word_count": word_count,
    }


# ---------------------------------------------------------------------------
# Step 4: cut the text into chunks
# ---------------------------------------------------------------------------

def split_long_paragraph(text):
    """Cut a paragraph longer than PIECE_MAX_WORDS into pieces, between sentences."""
    # A sentence ends with . ! or ? followed by a space and a capital letter or number.
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
    """Group paragraphs into chunks of about 300-500 words, with overlap.

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

    chunks = []
    current = []        # the texts in the chunk being built
    current_words = 0
    first_page = None   # page of the first new piece in the chunk
    last_page = None

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


# ---------------------------------------------------------------------------
# Step 5: store the chunks in ChromaDB
# ---------------------------------------------------------------------------

def open_database():
    """Open (or create) the ChromaDB database in data/chroma/."""
    DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)
    # anonymized_telemetry=False: don't send usage statistics to ChromaDB's makers.
    return chromadb.PersistentClient(
        path=str(DATABASE_FOLDER),
        settings=Settings(anonymized_telemetry=False),
    )


def ingest(rebuild=False):
    """Index every PDF in papers/ that isn't in the database yet."""
    pdf_files = sorted(PAPERS_FOLDER.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {PAPERS_FOLDER}")
        return

    client = open_database()
    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
            print("Deleted the old index (--rebuild).")
        except Exception:
            pass  # there was no index yet, nothing to delete

    # Uses ChromaDB's default embedding model. The first time, it downloads it (~80 MB).
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    new_papers = 0
    new_chunks = 0
    skipped = []
    low_text = []   # (file name, words per page)
    failed = []     # (file name, error message)

    for pdf_path in pdf_files:
        # Already indexed? Then skip it. (Use --rebuild to start over.)
        already = collection.get(where={"file_name": pdf_path.name}, limit=1)
        if already["ids"]:
            skipped.append(pdf_path.name)
            continue

        try:
            paper = extract_paper(pdf_path)
        except Exception as error:
            failed.append((pdf_path.name, str(error)))
            print(f"  ! {pdf_path.name}: could not be read ({error})")
            continue

        words_per_page = paper["word_count"] / max(paper["num_pages"], 1)
        if words_per_page < LOW_TEXT_WORDS_PER_PAGE:
            low_text.append((pdf_path.name, round(words_per_page)))

        chunks = make_chunks(paper["paragraphs"])
        if not chunks:
            print(f"  ! {pdf_path.name}: no text found, nothing stored")
            continue

        # Each chunk is stored with its text, a unique id, and "metadata"
        # (extra information we show later as the source).
        ids = []
        metadatas = []
        for number, chunk in enumerate(chunks):
            chunk_id = f"{pdf_path.name}::chunk-{number}"
            ids.append(chunk_id)
            metadatas.append({
                "title": paper["title"],
                "file_name": pdf_path.name,
                "page": chunk["page"],
                "page_end": chunk["page_end"],
                "chunk_id": chunk_id,
            })
        collection.add(ids=ids, documents=[c["text"] for c in chunks], metadatas=metadatas)

        new_papers += 1
        new_chunks += len(chunks)
        print(f"  + {paper['title'][:70]}  ({paper['num_pages']} pages, {len(chunks)} chunks)")

    # --- Summary --------------------------------------------------------------
    print()
    print("=== Summary ===")
    print(f"PDFs in papers/:        {len(pdf_files)}")
    print(f"Newly indexed:          {new_papers}  ({new_chunks} chunks)")
    print(f"Already indexed:        {len(skipped)}  (skipped)")
    print(f"Chunks in the index:    {collection.count()}")

    if low_text:
        print()
        print("Please check these PDFs. Little or no text was found (maybe scanned images):")
        for name, wpp in low_text:
            print(f"  - {name}  (about {wpp} words per page)")
    if failed:
        print()
        print("These PDFs could not be read:")
        for name, error in failed:
            print(f"  - {name}: {error}")


# ---------------------------------------------------------------------------
# --preview: show what the cleaned text of one PDF looks like
# ---------------------------------------------------------------------------

def preview(file_name):
    """Save the cleaned text of one PDF in preview.txt, so you can check the extraction.

    The summary is also printed in the terminal.
    """
    pdf_path = Path(file_name)
    if not pdf_path.exists():
        pdf_path = PAPERS_FOLDER / file_name  # allow just the name of a file in papers/
    if not pdf_path.exists():
        print(f"File not found: {file_name}")
        return

    paper = extract_paper(pdf_path)
    chunks = make_chunks(paper["paragraphs"])

    # The summary box at the top
    summary = ["=" * 70]
    summary.append(f"File:        {pdf_path.name}")
    summary.append(f"Title:       {paper['title']}   (from {paper['title_source']})")
    summary.append(f"Pages:       {paper['num_pages']}")
    summary.append(f"Words kept:  {paper['word_count']}")
    if paper["start"]:
        page, heading = paper["start"]
        summary.append(f"Starts at:   '{heading}...' on page {page} (title/author part skipped)")
    else:
        summary.append("Starts at:   page 1 (no Abstract/Introduction heading found, nothing skipped)")
    if paper["references_page"]:
        summary.append(f"References:  start on page {paper['references_page']} (skipped)")
    else:
        summary.append("References:  no reference heading found (nothing skipped)")
    summary.append(f"Chunks:      {len(chunks)}  (word counts: {[len(c['text'].split()) for c in chunks]})")
    if paper["removed"]:
        summary.append("Removed as header/footer:")
        for text in paper["removed"][:10]:
            summary.append(f"   - {text[:80]}")
    summary.append("=" * 70)

    # Write the summary and then the full cleaned text, page by page, to preview.txt.
    # encoding="utf-8" makes special characters (like – or é) show correctly.
    with open(PREVIEW_FILE, "w", encoding="utf-8") as file:
        file.write("\n".join(summary) + "\n")
        current_page = None
        for page, text in paper["paragraphs"]:
            if page != current_page:
                file.write(f"\n----- page {page} -----\n\n")
                current_page = page
            file.write(text + "\n\n")

    print("\n".join(summary))
    print(f"The full cleaned text is saved in {PREVIEW_FILE.name}. Open it in VS Code to read it.")


# ---------------------------------------------------------------------------
# Start here when the file is run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Print special characters (like é or –) correctly, also when saving to a file.
    sys.stdout.reconfigure(encoding="utf-8")
    # Hide MuPDF's low-level warnings about slightly broken PDFs.
    pymupdf.TOOLS.mupdf_display_errors(False)

    parser = argparse.ArgumentParser(description="Build the search index from the PDFs in papers/.")
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--rebuild", action="store_true",
                        help="delete the index and build it again from all PDFs")
    choice.add_argument("--preview", metavar="FILE",
                        help="save the cleaned text of one PDF in preview.txt (nothing is indexed)")
    args = parser.parse_args()

    if args.preview:
        preview(args.preview)
    else:
        ingest(rebuild=args.rebuild)
