"""
ingest.py - builds the search index from the research papers.

What it does, step by step:
  1. Opens every PDF in the papers/ folder and takes out the clean text   (core/pdf_text.py)
  2. Cuts the text into "chunks" of about 500-700 words                   (core/chunks.py)
  3. Turns each chunk into an embedding (numbers for searching)           (core/embeddings.py)
  4. Saves the chunks in the search index, in data/chroma/                (core/database.py)

Ollama must be running: it makes the embeddings (model: EMBEDDING_MODEL in settings.py).

How to run it (inside the Chatbot folder, with the virtual environment on):
  python ingest.py                       add new PDFs to the index
  python ingest.py --rebuild             delete the index and build it again
  python ingest.py --preview FILE.pdf    save the cleaned text of one PDF in data/preview.txt
                                         (nothing is added to the index)
"""

import argparse
import sys
from pathlib import Path

import pymupdf

from core.chunks import make_chunks
from core.database import index_matches_model, open_collection, open_database
from core.embeddings import embed_documents
from core.errors import ChatbotError
from core.pdf_text import extract_paper
from settings import COLLECTION_NAME, EMBEDDING_MODEL, LOW_TEXT_WORDS_PER_PAGE, PAPERS_FOLDER, PREVIEW_FILE


def paper_name(pdf_path):
    """The name a paper is stored under: its place inside papers/, e.g. "Pro AI/Generative AI at Work.pdf".

    Including the folder means two papers with the same file name in different folders don't get mixed up.
    """
    return pdf_path.relative_to(PAPERS_FOLDER).as_posix()   # as_posix: always "/" between folders


def paper_folder(pdf_path):
    """The subfolder of papers/ a paper is in, e.g. "Pro AI" ("" for a PDF directly in papers/)."""
    folder = pdf_path.parent.relative_to(PAPERS_FOLDER).as_posix()
    return "" if folder == "." else folder


def ingest(rebuild=False):
    """Index every PDF in papers/ (and its subfolders) that isn't in the index yet."""
    # rglob = search this folder AND all folders inside it ("recursive glob").
    pdf_files = sorted(PAPERS_FOLDER.rglob("*.pdf"))
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

    collection = open_collection(client)
    # An index made with another embedding model can't be added to: its numbers don't compare.
    if not index_matches_model(collection):
        print(f"The index was built with another embedding model than {EMBEDDING_MODEL}.")
        print("Run:  python ingest.py --rebuild")
        return

    new_papers = 0
    new_chunks = 0
    skipped = []
    low_text = []   # (file name, words per page)
    failed = []     # (file name, error message)

    for pdf_path in pdf_files:
        name = paper_name(pdf_path)

        # Already indexed? Then skip it. (Use --rebuild to start over.)
        # where= searches the chunks' extra information: is there one chunk from this file?
        already = collection.get(where={"file_name": name}, limit=1)
        if already["ids"]:
            skipped.append(name)
            continue

        try:
            paper = extract_paper(pdf_path)
        except Exception as error:
            failed.append((name, str(error)))
            print(f"  ! {name}: could not be read ({error})")
            continue

        words_per_page = paper["word_count"] / max(paper["num_pages"], 1)
        if words_per_page < LOW_TEXT_WORDS_PER_PAGE:
            low_text.append((name, round(words_per_page)))

        chunks = make_chunks(paper["paragraphs"])
        if not chunks:
            print(f"  ! {name}: no text found, nothing stored")
            continue

        # Each chunk is stored with its text, a unique id, and "metadata"
        # (extra information we show later as the source).
        ids = []
        metadatas = []
        for number, chunk in enumerate(chunks):
            chunk_id = f"{name}::chunk-{number}"
            ids.append(chunk_id)
            metadatas.append({
                "title": paper["title"],
                "file_name": name,
                "folder": paper_folder(pdf_path),
                "page": chunk["page"],
                "page_end": chunk["page_end"],
                "chunk_id": chunk_id,
            })
        # Make the embeddings (Ollama, a few seconds per paper), then save everything at once.
        texts = [c["text"] for c in chunks]
        try:
            embeddings = embed_documents(texts)
        except ChatbotError as error:
            print(f"\nStopped: {error}")
            return
        collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)

        new_papers += 1
        new_chunks += len(chunks)
        print(f"  + {paper['title'][:70]}  ({paper['num_pages']} pages, {len(chunks)} chunks)")

    # --- Summary --------------------------------------------------------------
    print()
    print("=== Summary ===")
    print(f"PDFs in papers/:        {len(pdf_files)}  (including subfolders)")
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


def preview(file_name):
    """Save the cleaned text of one PDF in data/preview.txt, so you can check the extraction.

    The summary is also printed in the terminal.
    """
    pdf_path = Path(file_name)
    if not pdf_path.exists():
        pdf_path = PAPERS_FOLDER / file_name  # a name inside papers/, like "Pro AI/paper.pdf"
    if not pdf_path.exists():
        # Just the file name, without its folder: look for it in all the subfolders.
        found = sorted(PAPERS_FOLDER.rglob(Path(file_name).name))
        if not found:
            print(f"File not found: {file_name}")
            return
        pdf_path = found[0]

    paper = extract_paper(pdf_path)
    chunks = make_chunks(paper["paragraphs"])

    # The summary box at the top
    summary = ["=" * 70]
    summary.append(f"File:        {paper_name(pdf_path) if PAPERS_FOLDER in pdf_path.parents else pdf_path.name}")
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

    # Write the summary and then the full cleaned text, page by page, to the preview file.
    # encoding="utf-8" makes special characters (like – or é) show correctly.
    PREVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PREVIEW_FILE, "w", encoding="utf-8") as file:
        file.write("\n".join(summary) + "\n")
        current_page = None
        for page, text in paper["paragraphs"]:
            if page != current_page:
                file.write(f"\n----- page {page} -----\n\n")
                current_page = page
            file.write(text + "\n\n")

    print("\n".join(summary))
    print("The full cleaned text is saved in data/preview.txt. Open it in VS Code to read it.")


if __name__ == "__main__":
    # Print special characters (like é or –) correctly, also when saving to a file.
    sys.stdout.reconfigure(encoding="utf-8")
    # Hide MuPDF's low-level warnings about slightly broken PDFs.
    pymupdf.TOOLS.mupdf_display_errors(False)

    # argparse reads the options typed after "python ingest.py" (like --rebuild), and makes
    # "python ingest.py --help" show them. "Mutually exclusive" = you can use one of them, not both.
    parser = argparse.ArgumentParser(description="Build the search index from the PDFs in papers/.")
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--rebuild", action="store_true",
                        help="delete the index and build it again from all PDFs")
    choice.add_argument("--preview", metavar="FILE",
                        help="save the cleaned text of one PDF in data/preview.txt (nothing is indexed)")
    args = parser.parse_args()

    if args.preview:
        preview(args.preview)
    else:
        ingest(rebuild=args.rebuild)
