"""
rag.py - the "brain" of the chatbot. It answers one question in two steps:

  1. Retrieve: find the 6 chunks in the database that best match the question.
  2. Generate: send the question and those chunks to an AI model, which writes
     an answer using only those chunks, with sources.

The AI model can be:
  - Ollama: free, runs on your own computer (the default)
  - Claude: Anthropic's model, paid per question, better answers
Which one is used is set in .env with LLM_PROVIDER (see README: "Choosing the AI model").

This file doesn't run on its own. It is used by ask.py (questions in the
terminal) and later by api.py (questions from the website).
"""

import os
import re

import anthropic
import ollama
from dotenv import load_dotenv

from ingest import COLLECTION_NAME, HERE, open_database


# Read the settings in .env (which AI to use, model names, API key) into the environment.
load_dotenv(HERE / ".env")


# ---------------------------------------------------------------------------
# Settings (change these if you want)
# ---------------------------------------------------------------------------

# The instructions Claude gets before every question. Edit freely.
SYSTEM_PROMPT = """You are an assistant that answers questions about artificial intelligence and \
Hybrid Intelligence (collaboration between humans and AI). Answer using ONLY the \
research excerpts provided. For every claim, cite the paper it came from as \
[Paper title, p. X]. When a question concerns benefits, risks or ethics of AI, \
give a balanced answer and note where papers disagree. If the excerpts do not \
contain the answer, say clearly that the papers you have don't cover it rather \
than guessing. Write clearly for a general audience."""

# Extra rules sent together with every question, right after the excerpts.
# Small models follow short, concrete rules best when they come next to the question.
ANSWER_RULES = """Rules for your answer:
- Explain in your own words. Do not copy long passages from the excerpts.
- Keep it to about 150-250 words.
- Use only the excerpts that are relevant to the question. Ignore the others.
- Cite as [Paper title, p. X], copying the paper title exactly as written above."""

# How many chunks to retrieve for each question.
NUMBER_OF_CHUNKS = 6

# Used when .env doesn't say otherwise.
DEFAULT_PROVIDER = "ollama"
DEFAULT_OLLAMA_MODEL = "gemma3:4b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_CLAUDE_MODEL = "claude-opus-5-5"

# --- Ollama only ---
# How much text the model can read at once, in tokens (1 token is about 3/4 of a word).
# The 6 excerpts + instructions are about 5,000 tokens. Ollama's normal limit is
# smaller, and it would then silently cut off part of the excerpts.
OLLAMA_CONTEXT_SIZE = 8192

# --- Claude only ---
# How hard Claude thinks before answering: "low", "medium", "high", "xhigh" or "max".
# Higher = more careful answers, but slower and more expensive.
EFFORT = "medium"

# The longest answer Claude may write, in tokens.
# This is an upper limit, not a target: normal answers are much shorter.
MAX_TOKENS = 16000

# Models that support Anthropic's automatic "fallback": if a safety filter
# wrongly blocks a question, Anthropic tries again with another model.
MODELS_WITH_FALLBACK = ("claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5")


class ChatbotError(Exception):
    """A problem with a friendly message we can show to the user."""


# ---------------------------------------------------------------------------
# Step 1: retrieve the best-matching chunks
# ---------------------------------------------------------------------------

_collection = None  # the database is opened once, then reused


def get_collection():
    """Open the ChromaDB collection (only the first time) and return it."""
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


# ---------------------------------------------------------------------------
# Step 2: ask the AI model to answer from the chunks
# ---------------------------------------------------------------------------

def build_message(question, chunks):
    """Put the excerpts and the question together into the message for the AI model."""
    parts = ["Research excerpts:\n"]
    for chunk in chunks:
        parts.append(
            "---\n"
            f"Paper title: {chunk['title']}\n"
            f"Page: {page_label(chunk)}\n"
            f"{chunk['text']}\n"
        )
    parts.append(ANSWER_RULES + "\n\n" + f"Question: {question}")
    return "\n".join(parts)


def ask_ai(message):
    """Send the message to the AI model chosen in .env and return its answer."""
    provider = (os.getenv("LLM_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    if provider == "ollama":
        return ask_ollama(message)
    if provider == "anthropic":
        return ask_claude(message)
    raise ChatbotError(f"Unknown LLM_PROVIDER '{provider}' in .env. Use 'ollama' or 'anthropic'.")


def ask_ollama(message):
    """Send the message to a model running in Ollama on this computer."""
    model = os.getenv("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL
    client = ollama.Client(host=os.getenv("OLLAMA_URL") or DEFAULT_OLLAMA_URL)

    try:
        response = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            options={"num_ctx": OLLAMA_CONTEXT_SIZE},
        )
    except ConnectionError:
        raise ChatbotError("Could not reach Ollama. Is the Ollama app running? (see README)")
    except ollama.ResponseError as error:
        if error.status_code == 404:
            raise ChatbotError(f"The model '{model}' isn't downloaded yet. Run: ollama pull {model}")
        raise ChatbotError(f"Ollama returned an error: {error.error}")

    answer = response.message.content or ""
    # Some models write out their thinking between <think> tags first. Remove it.
    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL)
    return answer.strip()


def ask_claude(message):
    """Send the message to Claude (Anthropic, paid) and return the text of its answer."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "your-key-goes-here":
        raise ChatbotError("No API key found. Put your key in the .env file (see README).")
    model = os.getenv("ANTHROPIC_MODEL") or DEFAULT_CLAUDE_MODEL

    client = anthropic.Anthropic(api_key=api_key)

    # The settings for the request. "fallbacks" is a newer (beta) feature, so it
    # is only added for models that support it.
    request = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": message}],
        "output_config": {"effort": EFFORT},
    }
    if model in MODELS_WITH_FALLBACK:
        request["betas"] = ["server-side-fallback-2026-07-01"]
        request["fallbacks"] = "default"

    try:
        response = client.beta.messages.create(**request)
    except anthropic.AuthenticationError:
        raise ChatbotError("The API key was not accepted. Check ANTHROPIC_API_KEY in .env.")
    except anthropic.NotFoundError:
        raise ChatbotError(f"The model '{model}' was not found. Check ANTHROPIC_MODEL in .env.")
    except anthropic.RateLimitError:
        raise ChatbotError("Too many questions at once. Please wait a minute and try again.")
    except anthropic.APIConnectionError:
        raise ChatbotError("Could not reach Anthropic. Check your internet connection.")
    except anthropic.APIStatusError as error:
        raise ChatbotError(f"Anthropic returned an error ({error.status_code}). Please try again later.")

    if response.stop_reason == "refusal":
        raise ChatbotError("Sorry, I can't answer that question.")

    # The answer can come in several pieces ("blocks"). Keep only the text pieces.
    return "".join(block.text for block in response.content if block.type == "text").strip()


def fix_excerpt_citations(answer, chunks):
    """Small models sometimes cite "[Excerpt 2, p. 4]" instead of the paper title.

    This puts the real title in its place: "[Hybrid Intelligence, p. 4]".
    """
    def to_title(match):
        number = int(match.group(1))
        if 1 <= number <= len(chunks):
            return chunks[number - 1]["title"]
        return match.group(0)  # a number we don't know: leave it as it is

    return re.sub(r"\bExcerpt\s+(\d+)(?=,\s*pp?\.)", to_title, answer)


def find_sources(answer, chunks):
    """Find which papers the answer actually cites, and which pages.

    Looks in the answer for "<exact paper title>, p. X". Returns a list like:
      [{"title": "...", "file_name": "...", "pages": ["3", "5-6"]}, ...]
    """
    sources = []
    seen_titles = set()
    for chunk in chunks:
        title = chunk["title"]
        if title in seen_titles:
            continue
        seen_titles.add(title)

        # e.g. "Hybrid Intelligence, p. 3" or "Hybrid Intelligence, pp. 3-4"
        pattern = re.escape(title) + r",\s*pp?\.\s*([\d\-–, ]+\d)"
        pages = []
        for found in re.findall(pattern, answer):
            for page in found.split(","):
                page = page.strip()  # remove spaces around the number
                if page and page not in pages:
                    pages.append(page)
        if pages:
            # Sort by the first number, then shortest first: "2", "5", "5-6", "7"
            pages.sort(key=lambda page: (int(re.match(r"\d+", page).group()), len(page)))
            sources.append({"title": title, "file_name": chunk["file_name"], "pages": pages})
    return sources


def answer_question(question):
    """Answer one question. This is the function ask.py and api.py use.

    Returns a dictionary with:
      answer  - the text the AI model wrote
      sources - the papers (and pages) cited in the answer
      chunks  - the excerpts that were retrieved (for checking with --show-chunks)
    """
    chunks = retrieve(question)
    answer = ask_ai(build_message(question, chunks))
    answer = fix_excerpt_citations(answer, chunks)
    return {"answer": answer, "sources": find_sources(answer, chunks), "chunks": chunks}
