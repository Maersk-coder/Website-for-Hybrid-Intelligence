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
PAPERS_FOLDER = HERE / "papers"                     # your PDFs (subfolders are fine)
TITLES_FILE = PAPERS_FOLDER / "titles.txt"          # titles you set yourself, when the automatic one is wrong
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

# A "References" heading only counts after this part of the paper (0.3 = after the first 30% of
# the pages), so one in a table of contents is ignored. Papers with a long appendix after the
# references (e.g. "Generative AI at Work": references on page 38 of 106) need it this low.
REFERENCES_FROM_SHARE = 0.3


# ---------------------------------------------------------------------------
# Cutting the text into chunks (core/chunks.py)
# ---------------------------------------------------------------------------

# Medium-sized chunks: big enough to keep a thought together, small enough that each chunk is about
# one thing, so it matches a specific question well. (Was 500-700 words; very long chunks mix
# several topics, which makes the search less precise.)
CHUNK_MIN_WORDS = 250   # a chunk is not closed before it has this many words
CHUNK_MAX_WORDS = 400   # ...and never grows past this many
OVERLAP_WORDS = 50      # each chunk starts with the last 50 words of the one before,
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
# (Based on the scores in tests/results/2026-10-22_1824.md: answers were too long and too academic,
#  and "not covered" answers went off on a tangent.)
ANSWER_RULES = """Rules for your answer:
- Start directly with the answer. Never talk about the question or about yourself
  (no "You asked...", "Based on the provided research...").
- Write for people who know nothing about this topic: use everyday words and short sentences.
  Avoid technical terms, or explain them in a few words.
- Keep it short: 3 to 5 sentences. A question about a fact (how many, when, who) gets 1 or 2 sentences.
  The visitor can always ask for more.
- When it helps, give one concrete example from the excerpts (a study, a number, a real case).
- If the visitor asks for more about your previous answer ("elaborate", "tell me more", "why"),
  do NOT repeat what you already said: add new details, examples or explanations from the excerpts.
- Explain in your own words. Do not copy long passages from the excerpts.
- Use only the excerpts that are relevant to the question. Ignore the others.
- Cite every claim with the title and page, for example: {example}
  Write the title exactly as it is written above. Never write the words "Paper title" in a citation.
- If the excerpts don't answer the question, reply in 1 or 2 short sentences: say that your research
  papers don't cover this and suggest searching elsewhere, like Google. Then invite the visitor to ask
  anything else about Hybrid Intelligence or AI. Don't explain why, don't cite anything, add nothing else."""

# How many chunks (excerpts) are found and sent with each question.
# (8 medium chunks is about as much text as the 6 long ones before.)
NUMBER_OF_CHUNKS = 8

# At most this many of those chunks may come from the same paper, so one long paper can't fill all
# the places and the AI sees several papers' points of view. To find enough, the search looks at the
# best SEARCH_CANDIDATES chunks. (MAX_CHUNKS_PER_PAPER = NUMBER_OF_CHUNKS switches the limit off.)
MAX_CHUNKS_PER_PAPER = 4
SEARCH_CANDIDATES = 25

# The Ollama model that makes the embeddings (the numbers the search compares).
# Download it once with:  ollama pull nomic-embed-text
# After changing it, rebuild the index:  python ingest.py --rebuild
EMBEDDING_MODEL = "nomic-embed-text"

# Questions that have nothing to do with the papers (like "What is the best pizza in Rome?") get this
# fixed answer straight away, without asking the AI. A question counts as off-topic when even the
# closest excerpt is further away than OFF_TOPIC_DISTANCE. Measured with nomic-embed-text on 2026-10-23:
# off-topic questions 0.80-1.07 (pizza, weather, homework, bread, a joke), real questions 0.42-0.74
# ("Who wrote the manifesto?" 0.74), AI questions the papers don't cover ~0.64.
# Lower = more questions count as off-topic. (9 = switch it off.) Measure again after changing
# EMBEDDING_MODEL. Check a question's distance with:  python ask.py --show-chunks
OFF_TOPIC_DISTANCE = 0.77
OFF_TOPIC_ANSWER = ("That's not something I can help with. Try a search engine like Google instead. "
                    "You're welcome to ask me anything about Hybrid Intelligence or AI!")

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
