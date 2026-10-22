"""
core/pdf_text.py - read one PDF and get its clean text, page by page.

What happens to the text:
  - headers and footers that repeat on many pages are removed, and so are page numbers
  - words broken over two lines are joined again ("collab-" + "oration")
  - the title page part (title, authors, addresses) is skipped, if an Abstract/Introduction heading is found
  - everything from the "References" heading onwards is skipped
  - the paper's title is found (PDF information, else the biggest text on page 1, else the file name)

Look here when: the text looks strange, headers are left in, or a title is wrong.
Check a PDF with:  python ingest.py --preview "file.pdf"
"""

import re
from collections import Counter

import pymupdf  # PyMuPDF: reads PDF files

from settings import MARGIN_SHARE, REPEAT_SHARE


# ---------------------------------------------------------------------------
# Patterns used for cleaning (regular expressions)
# ---------------------------------------------------------------------------
# A regular expression ("regex") describes a text pattern. The most used signs below:
#   ^ = the start of the text     $ = the end       \d = a digit       \s = a space
#   ? = the part before it is optional      a|b = a or b      ( ) = a group
#   re.IGNORECASE = capital letters or not doesn't matter

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
# Small helpers
# ---------------------------------------------------------------------------

def clean_block(text):
    """Clean one block of text (roughly one paragraph) taken from a PDF."""
    for joined, plain in LIGATURES.items():
        text = text.replace(joined, plain)

    # A "soft hyphen" is an invisible hyphen used for line breaks. Remove it.
    text = text.replace("­\n", "").replace("­", "")

    # Join words broken over two lines: "collab-\noration" -> "collaboration".
    # Only when the next line starts with a small letter...
    # (re.sub = find and replace. (\w) and ([a-z]) are groups: the letter before the "-" and
    #  the letter after the line break. \1\2 puts those two letters back, without the "-" and break.)
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


# ---------------------------------------------------------------------------
# Finding the title
# ---------------------------------------------------------------------------

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
    # get_text("dict") describes the page in layers: blocks (paragraphs) contain lines,
    # and lines contain "spans" (pieces of text in one font and size). bbox = the span's box on the page.
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


# ---------------------------------------------------------------------------
# Reading the whole paper
# ---------------------------------------------------------------------------

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
        # Each block comes as 7 values: its box on the page (x0, y0 = top-left corner,
        # x1, y1 = bottom-right corner; y grows downwards), its text, its number and its type.
        for x0, y0, x1, y1, text, block_no, block_type in page.get_text("blocks"):
            if block_type != 0:  # 0 = text, 1 = image
                continue
            in_margin = y1 < height * MARGIN_SHARE or y0 > height * (1 - MARGIN_SHARE)
            blocks.append({"raw": text, "text": clean_block(text), "in_margin": in_margin})
        pages.append(blocks)
    doc.close()

    # --- Find headers/footers: text in the margins that repeats on many pages ---
    # A Counter is a dictionary that counts: margin_counts["journal of ai"] = on how many pages it was.
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
            # (page, block) pairs compare like dates: first the page number, then the block number.
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
        # For the preview: the page number (counting from 1) and the first 40 letters of the heading
        "start": (start[0] + 1, pages[start[0]][start[1]]["text"][:40]) if start else None,
        "references_page": references_page,
        "word_count": word_count,
    }
