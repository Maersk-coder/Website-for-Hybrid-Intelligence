"""
core/ai_model.py - talk to the AI model that writes the answers: Ollama, running on this computer.

Look here when: the chat says it can't reach Ollama, or the model is missing.
(Quickest check: python check.py)
"""

import httpx  # the package Ollama uses to connect (installed together with ollama)
import ollama

from core.errors import ChatbotError
from settings import OLLAMA_CONTEXT_SIZE, OLLAMA_MODEL, OLLAMA_THINK, OLLAMA_URL, SYSTEM_PROMPT


def model_description():
    """A short description of the AI in use, e.g. "ollama / qwen3.5:4b"."""
    return "ollama / " + OLLAMA_MODEL


def stream_answer(message, history):
    """Send the message (plus the earlier conversation) to Ollama.

    Gives back the answer piece by piece (a few words at a time) while the model
    writes it, so it can be shown straight away.

    This is a "generator": because it uses "yield" instead of "return", it doesn't give back
    one finished answer, but hands out each piece the moment it arrives, to whoever loops
    over it ("for piece in stream_answer(...)" in core/answers.py).
    """
    client = ollama.Client(host=OLLAMA_URL)
    try:
        pieces = client.chat(
            model=OLLAMA_MODEL,
            # The messages, each with a "role": "system" = the instructions, "user" = a question,
            # "assistant" = an earlier answer. The instructions first, then the earlier
            # conversation, then the new message.
            messages=[{"role": "system", "content": SYSTEM_PROMPT}]
                     + history
                     + [{"role": "user", "content": message}],
            think=OLLAMA_THINK,
            options={"num_ctx": OLLAMA_CONTEXT_SIZE},
            stream=True,  # get the answer in pieces while it's being written
        )
        for piece in pieces:
            if piece.message.content:
                yield piece.message.content
    except (ConnectionError, httpx.ConnectError):
        # Ollama isn't running (not started, or busy updating itself).
        # ConnectionError is what Ollama gives for a normal answer, httpx.ConnectError for a streamed one.
        raise ChatbotError("Could not reach Ollama. Is the Ollama app running? (see README)")
    except ollama.ResponseError as error:
        if error.status_code == 404:
            raise ChatbotError(f"The model '{OLLAMA_MODEL}' isn't downloaded yet. Run: ollama pull {OLLAMA_MODEL}")
        if "does not support thinking" in str(error.error):
            raise ChatbotError(f"The model '{OLLAMA_MODEL}' can't think step by step. Set OLLAMA_THINK=false in .env.")
        raise ChatbotError(f"Ollama returned an error: {error.error}")
