"""
api.py - a small web server, so the website's chat panel can talk to the chatbot.

The website sends a question to this server, the server answers it (core/answers.py:
search the papers + ask the AI) and sends back the answer and the sources.

Addresses ("endpoints") it has:
  POST /chat         send {"message": "...", "history": [...]}, get {"answer": "...", "sources": [...]}
  POST /chat/stream  the same, but the answer comes piece by piece while it is written (the chat panel uses this)
  GET  /health       check that the server is running
  GET  /docs         a test page FastAPI makes automatically, to try /chat in the browser

Problems are written to logs/server.log (with the date and time), so you can look
at them later, even after closing the terminal.

How to run it (inside the Chatbot folder, with the virtual environment on):
  python api.py
Then open http://127.0.0.1:8000/docs in your browser. Stop it with Ctrl+C.
"""

import json
import logging
import threading
import time
from collections import defaultdict, deque
from logging.handlers import RotatingFileHandler
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from core.ai_model import model_description
from core.answers import answer_question, answer_question_stream
from core.database import get_collection
from core.errors import ChatbotError
from settings import (
    ALLOWED_ORIGINS, LOG_FILE, MAX_MESSAGE_CHARS, RATE_LIMIT, RATE_WINDOW_SECONDS, SERVER_HOST, SERVER_PORT,
)


# ---------------------------------------------------------------------------
# The error log: problems go to the terminal AND to logs/server.log
# ---------------------------------------------------------------------------

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
log = logging.getLogger("chatbot")
log.setLevel(logging.INFO)
# The file is kept small: at 1 MB it starts a new one, and keeps the 3 newest old ones.
file_log = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
file_log.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s", "%Y-%m-%d %H:%M:%S"))
log.addHandler(file_log)
log.addHandler(logging.StreamHandler())  # also show it in the terminal


# ---------------------------------------------------------------------------
# The app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Hybrid Intelligence Chatbot",
    description="Answers questions about AI and Hybrid Intelligence from research papers.",
)

# Only the websites in ALLOWED_ORIGINS (in .env) may use this server from a browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# The shape of the data going in and out. FastAPI checks incoming data against
# these, and shows them on the /docs page.

class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]   # who said it: the visitor or the chatbot
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[HistoryMessage] = []   # the earlier conversation (can be empty)

    # The example that is already filled in on the /docs test page.
    model_config = {
        "json_schema_extra": {"examples": [{"message": "What is Hybrid Intelligence?", "history": []}]}
    }


class Source(BaseModel):
    title: str
    file_name: str
    pages: list[str]


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


# ---------------------------------------------------------------------------
# Rate limiting: at most RATE_LIMIT questions per visitor per RATE_WINDOW_SECONDS
# ---------------------------------------------------------------------------

# For each visitor (by IP address): the times of their recent questions.
# This is kept in memory, so it starts empty again when the server restarts.
recent_questions = defaultdict(deque)
# Several questions can be handled at the same time, so changes to
# recent_questions are done one at a time with this lock.
recent_questions_lock = threading.Lock()


def too_many_questions(visitor):
    """Return True if this visitor has asked too many questions recently."""
    now = time.time()
    with recent_questions_lock:
        times = recent_questions[visitor]
        # Forget questions older than the time window.
        while times and now - times[0] > RATE_WINDOW_SECONDS:
            times.popleft()
        if len(times) >= RATE_LIMIT:
            return True
        times.append(now)
        return False


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def check_question(body, request):
    """The checks every question goes through. Returns (message, history), or stops with an error."""
    visitor = request.client.host if request.client else "unknown"
    if too_many_questions(visitor):
        log.warning("Too many questions from %s", visitor)
        raise HTTPException(429, "You're asking questions very quickly. Please wait a minute and try again.")

    message = body.message.strip()
    if not message:
        raise HTTPException(400, "Please type a question.")
    if len(message) > MAX_MESSAGE_CHARS:
        raise HTTPException(400, f"Your question is too long. Please keep it under {MAX_MESSAGE_CHARS} characters.")

    history = [item.model_dump() for item in body.history]
    return message, history


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, request: Request):
    """Answer a question from the papers. Send the earlier conversation in "history"."""
    message, history = check_question(body, request)
    try:
        result = answer_question(message, history)
    except ChatbotError as error:
        # A known problem with a friendly message (e.g. Ollama is not running).
        log.warning("Question %r: %s", message[:80], error)
        raise HTTPException(503, str(error))
    except Exception:
        # An unexpected problem: the details go to the log, not to the visitor.
        log.exception("Unexpected error for question %r", message[:80])
        raise HTTPException(500, "Something went wrong on our side. Please try again.")

    return {"answer": result["answer"], "sources": result["sources"]}


@app.post("/chat/stream")
def chat_stream(body: ChatRequest, request: Request):
    """Like /chat, but the answer comes piece by piece while it is being written.

    The reply is a list of lines, sent one by one. Each line is a small JSON object:
      {"type": "text", "text": "a few words"}               a new piece of the answer
      {"type": "done", "answer": "...", "sources": [...]}   at the end: the full answer
                                                            (with citations repaired)
      {"type": "error", "detail": "a friendly message"}     if something went wrong
    """
    message, history = check_question(body, request)

    def lines():
        try:
            for kind, data in answer_question_stream(message, history):
                if kind == "text":
                    yield json.dumps({"type": "text", "text": data}) + "\n"
                else:
                    yield json.dumps({"type": "done", "answer": data["answer"], "sources": data["sources"]}) + "\n"
        except ChatbotError as error:
            log.warning("Question %r: %s", message[:80], error)
            yield json.dumps({"type": "error", "detail": str(error)}) + "\n"
        except Exception:
            log.exception("Unexpected error for question %r", message[:80])
            yield json.dumps({"type": "error", "detail": "Something went wrong on our side. Please try again."}) + "\n"

    # "ndjson" = newline-delimited JSON: one JSON object per line.
    return StreamingResponse(lines(), media_type="application/x-ndjson")


@app.get("/health")
def health():
    """Check that the server is running and the papers are indexed."""
    try:
        chunks = get_collection().count()
    except ChatbotError as error:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(error)})
    return {"status": "ok", "chunks_in_index": chunks, "model": model_description()}


@app.exception_handler(RequestValidationError)
def wrong_format(request, error):
    """Data in the wrong shape (e.g. no "message"): a short, friendly error instead of a long one."""
    return JSONResponse(
        status_code=422,
        content={"detail": 'The request was not in the right format. Send {"message": "your question"}.'},
    )


# ---------------------------------------------------------------------------
# Start the server when the file is run: python api.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print(f"Chatbot server starting. Test page: http://{SERVER_HOST}:{SERVER_PORT}/docs  (stop with Ctrl+C)")
    log.info("Server started (%s, allowed websites: %s)", model_description(), ", ".join(ALLOWED_ORIGINS) or "none")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
