"""
core/embeddings.py - turn text into "embeddings": lists of numbers that capture what a text is about.

Texts about similar things get similar numbers. That's how the search finds the chunks that
match a question: it compares the question's numbers with every chunk's numbers.

The embeddings are made by an Ollama model (EMBEDDING_MODEL in settings.py, normally
nomic-embed-text). It reads up to ~8,000 tokens, so it sees the whole chunk. (ChromaDB's own
standard model, used before, only read the first ~190 words of each chunk.)

Look here when: the search can't run ("Could not reach Ollama", "model isn't downloaded").
"""

import httpx
import ollama

from core.errors import ChatbotError
from settings import EMBEDDING_MODEL, OLLAMA_URL

# nomic-embed-text was trained with a label in front of each text, saying what kind of text it is.
# It matches a question to the right chunks best when we use the same labels.
QUESTION_LABEL = "search_query: "
DOCUMENT_LABEL = "search_document: "

# How many chunks are sent to Ollama at once while building the index.
BATCH_SIZE = 16


def _embed(texts):
    """Ask Ollama for the embeddings of a list of texts. Returns a list of number lists."""
    try:
        return ollama.Client(host=OLLAMA_URL).embed(model=EMBEDDING_MODEL, input=texts).embeddings
    except (ConnectionError, httpx.ConnectError):
        raise ChatbotError("Could not reach Ollama. Is the Ollama app running? (see README)")
    except ollama.ResponseError as error:
        if error.status_code == 404:
            raise ChatbotError(f"The model '{EMBEDDING_MODEL}' isn't downloaded yet. Run: ollama pull {EMBEDDING_MODEL}")
        raise ChatbotError(f"Ollama returned an error: {error.error}")


def embed_question(question):
    """The embedding of one question (used for every search)."""
    return _embed([QUESTION_LABEL + question])[0]


def embed_sentences(sentences):
    """The embeddings of a few sentences from an answer, to compare with the excerpts
    (used to add citations the AI forgot, see core/answers.py)."""
    return _embed([QUESTION_LABEL + sentence for sentence in sentences])


def embed_documents(texts):
    """The embeddings of many chunks (used when building the index), BATCH_SIZE at a time."""
    embeddings = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start + BATCH_SIZE]
        embeddings += _embed([DOCUMENT_LABEL + text for text in batch])
    return embeddings
