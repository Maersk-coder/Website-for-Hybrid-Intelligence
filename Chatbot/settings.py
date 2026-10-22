"""
settings.py - ALL the chatbot's settings and texts, in one place.

Change a number or a text here, and every part of the chatbot uses the new value.
Some settings come from the .env file (the AI model, the allowed websites):
those are read at the bottom of this file.

After changing a setting:
  - chunk sizes or PDF cleaning: rebuild the index with  python ingest.py --rebuild
  - anything else: restart the server (Ctrl+C, then python api.py)
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Folders and files
# ---------------------------------------------------------------------------

# Everything is found from where this file is, so it works no matter
# which folder you run the scripts from.
HERE = Path(__file__).parent
PAPERS_FOLDER = HERE / "papers"                     # your PDFs
DATABASE_FOLDER = HERE / "data" / "chroma"          # the search index (made by ingest.py)
PREVIEW_FILE = HERE / "data" / "preview.txt"        # where  ingest.py --preview  saves the cleaned text
LOG_FILE = HERE / "logs" / "server.log"             # where api.py writes down errors

# The name of the "collection" (like a table) in ChromaDB that holds the chunks.
COLLECTION_NAME = "papers"


# ---------------------------------------------------------------------------
# Reading the PDFs (core/pdf_text.py)
# ---------------------------------------------------------------------------

# Headers and footers are looked for in the top and bottom 10% of each page.
MARGIN_SHARE = 0.10

# A text counts as a repeated header/footer if it is on at least 30% of the pages.
REPEAT_SHARE = 0.30

# A PDF with fewer words than this per page is probably a scanned image.
LOW_TEXT_WORDS_PER_PAGE = 50


# ---------------------------------------------------------------------------
# Cutting the text into chunks (core/chunks.py)
# ---------------------------------------------------------------------------

CHUNK_MIN_WORDS = 500   # a chunk is not closed before it has this many words
CHUNK_MAX_WORDS = 700   # ...and never grows past this many
OVERLAP_WORDS = 100     # each chunk starts with the last 100 words of the one before,
                        # so a sentence cut at the edge is still found whole


# ---------------------------------------------------------------------------
# Answering a question (core/answers.py)
# ---------------------------------------------------------------------------

# The instructions the AI gets before every question. Edit freely.
SYSTEM_PROMPT = """You are an assistant that answers questions about artificial intelligence and \
Hybrid Intelligence (collaboration between humans and AI). Answer using ONLY the \
research excerpts provided. For every claim, cite the paper it came from as \
[Paper title, p. X]. When a question concerns benefits, risks or ethics of AI, \
give a balanced answer and note where papers disagree. If the excerpts do not \
contain the answer, say clearly that the papers you have don't cover it rather \
than guessing. Write clearly for a general audience."""

# Extra rules sent together with every question, right after the excerpts.
# Small models follow short, concrete rules best when they come next to the question.
# {example} is replaced with a real citation from the excerpts, e.g. [Hybrid Intelligence, p. 5].
ANSWER_RULES = """Rules for your answer:
- Explain in your own words. Do not copy long passages from the excerpts.
- Keep it to about 150-250 words.
- Use only the excerpts that are relevant to the question. Ignore the others.
- Cite every claim with the real title and page of the paper, for example: {example}
  Copy the title exactly. Never write the words "Paper title" in a citation."""

# How many chunks (excerpts) are found and sent with each question.
NUMBER_OF_CHUNKS = 6

# Conversation memory: how many earlier messages the AI sees (6 = the last 3
# questions and 3 answers), and the most characters kept from each one.
MAX_HISTORY_MESSAGES = 6
MAX_HISTORY_CHARS = 3000


# ---------------------------------------------------------------------------
# The AI model: Ollama (core/ai_model.py)
# ---------------------------------------------------------------------------

# How much text the model can read at once, in tokens (1 token is about 3/4 of a word).
# The 6 excerpts + instructions are about 5,000 tokens. Ollama's normal limit is
# smaller, and it would then silently cut off part of the excerpts.
OLLAMA_CONTEXT_SIZE = 8192


# ---------------------------------------------------------------------------
# The web server (api.py)
# ---------------------------------------------------------------------------

# Where the server runs. 127.0.0.1 = only this computer can reach it.
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000

# The longest question a visitor may send, in characters.
MAX_MESSAGE_CHARS = 1000

# Each visitor may ask at most RATE_LIMIT questions per RATE_WINDOW_SECONDS.
RATE_LIMIT = 10
RATE_WINDOW_SECONDS = 60


# ---------------------------------------------------------------------------
# Settings from the .env file (change them in .env, not here)
# ---------------------------------------------------------------------------

# load_dotenv copies the lines in .env into the "environment" (settings the computer keeps
# for a running program). os.getenv("NAME") then reads one. "or ..." gives the value to use
# when .env doesn't have that line.
load_dotenv(HERE / ".env")

# Which Ollama model writes the answers, and where Ollama runs.
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL") or "qwen3.5:4b"
OLLAMA_URL = os.getenv("OLLAMA_URL") or "http://localhost:11434"

# "Thinking" models (like Qwen) can first reason step by step before answering.
# That can give better answers, but is much slower on a laptop. Off unless .env says true.
OLLAMA_THINK = os.getenv("OLLAMA_THINK", "false").strip().lower() == "true"

# The websites allowed to use the server (separated by commas in .env).
# Browsers block other websites from calling it. This is called CORS.
# The line below cuts the text at every comma, removes spaces, and skips empty bits:
# "a.com, b.com" -> ["a.com", "b.com"]
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]
