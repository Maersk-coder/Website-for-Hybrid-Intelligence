# How the chatbot works as a server and a client

This page explains how the chatbot is split into a **client** (the chat panel on the website) and
a **server** (a Python program), how the two talk to each other, and which **web framework** the
server is built with: **FastAPI**, not Django, and why.

The project has **two servers**: the website is sent by **Django** (`hi_website/`, port 8001), and the
chatbot answers through **FastAPI** (`Chatbot/api.py`, port 8000). This page is mostly about the
chatbot. The Django side is explained in [hi_website/README.md](../hi_website/README.md).

How to start everything is in [the main README](../README.md#starting-everything). How to install the
chatbot is in [README.md](README.md). How to put it online is in [DEPLOYMENT.md](DEPLOYMENT.md).

## The short version

```
   VISITOR'S BROWSER (client)                         YOUR COMPUTER (server side)
 ┌──────────────────────────────┐  0. the page    ┌───────────────────────────────────────────┐
 │ Front_Page.html              │ ◄────────────── │ Django (hi_website/, port 8001)           │
 │  + chat-widget.js            │  (HTML, CSS,    │   sends the website and saves its forms   │
 │    (the chat panel)          │   JS, images)   └───────────────────────────────────────────┘
 │                              │
 │                              │  1. question    ┌───────────────────────────────────────────┐
 │                              │ ──────────────► │ api.py (FastAPI, port 8000)               │
 │                              │   HTTP + JSON   │   ├─► core/database.py ─► ChromaDB        │
 │                              │                 │   │     (finds 8 excerpts in data/chroma) │
 │                              │  2. answer,     │   └─► core/ai_model.py ─► Ollama          │
 │                              │ ◄────────────── │         (qwen3.5:4b writes the answer)    │
 │                              │  piece by piece │                                           │
 └──────────────────────────────┘                 └───────────────────────────────────────────┘
```

- The **client** is everything that runs in the visitor's browser: the web page and the chat
  panel (`widget/chat-widget.js` and `widget/chat-widget.css`). It shows the conversation, but it
  knows nothing about the papers and can't answer anything by itself.
- **Django** sends the page first (step 0). It doesn't take part in the chat.
- The **chatbot server** is `api.py`, a Python program that waits for questions. It searches the
  papers, asks the AI model, and sends back the answer with its sources.

## Why a server is needed at all

In the browser, the website is HTML, CSS and JavaScript. A browser can't run the chatbot itself, because:

1. **The browser can't run Python.** The chatbot (reading PDFs, the search, the citations) is
   written in Python.
2. **The heavy parts can't be sent to every visitor.** The search index (`data/chroma`) and the
   AI model (several gigabytes) stay on one computer, and every visitor uses them from there.
3. **The papers stay private.** The PDFs are protected by copyright. The server only sends out
   short answers and citations, never the papers themselves.

So the work is split: the browser does what browsers are good at (showing things and reacting to
clicks), and the server does the computing.

## What happens when a visitor asks a question

| Step | Where | What happens |
|---|---|---|
| 1 | Browser, `chat-widget.js` | The visitor types a question. The panel sends it to the server with `fetch(...)`: a **POST request** to `http://127.0.0.1:8000/chat/stream`, with the question and the earlier conversation as **JSON** (`{"message": "...", "history": [...]}`). |
| 2 | Server, `api.py` | FastAPI receives the request and checks it: is it the right format, not too long, and is this visitor not asking too often (max 10 per minute)? If not, it sends back an error code, like 400 or 429. |
| 3 | Server, `core/answers.py` | The question is handed to the chatbot's "brain". `core/database.py` finds the 8 best excerpts from the papers in ChromaDB. |
| 4 | Server, `core/ai_model.py` | The excerpts and the question go to **Ollama**, which runs the AI model and writes the answer word by word. |
| 5 | Server, `api.py` | Every few words are sent straight back to the browser (**streaming**), one small JSON line at a time: `{"type": "text", "text": "Hybrid"}`. At the end comes one `{"type": "done", ...}` line with the full answer (citations repaired) and the sources. |
| 6 | Browser, `chat-widget.js` | The panel reads the lines as they arrive and shows the words, so the visitor sees the first words after about 10 seconds instead of waiting a whole minute. At the end it shows the citation tags and the Sources box. |

### The words used above

- **HTTP**: the language browsers and servers use to talk. The browser sends a *request* and
  the server sends a *response*. Every web page you open works like this.
- **POST / GET**: the kind of request. GET means "give me something" (`/health`). POST means
  "here is some data, do something with it" (`/chat`).
- **Endpoint**: an address on the server that does one job, like `/chat`, `/chat/stream` or `/health`.
- **JSON**: a text format for data that both JavaScript and Python can read, e.g. `{"message": "What is Hybrid Intelligence?"}`.
- **API** (Application Programming Interface): a set of endpoints that is meant for *programs*,
  not for people. The chat panel is the program that uses this one. That's why `api.py` has that name.
- **Status code**: a number in each response that says how it went: 200 = OK, 400 = bad question,
  429 = too many questions, 503 = the AI isn't running.

### Two more servers, behind the scenes

`api.py` is a server for the browser, but it is also a **client** itself:

- **Ollama** is a server too. It runs in the background at `http://localhost:11434`, and
  `core/ai_model.py` and `core/embeddings.py` send it requests, just like the browser sends
  requests to `api.py`. So the chain is: browser → `api.py` → Ollama.
- **ChromaDB** is *not* a separate server here. It runs inside `api.py` and simply reads its
  files in `data/chroma`.

And the page itself comes from a third server, **Django** (`hi_website/`, port 8001). The chat panel
is loaded as part of that page, but its questions go straight to `api.py`, not through Django.

### Security between client and server

- **CORS**: the browser only lets a web page talk to a server at a *different* address if the
  server allows it. `api.py` only allows the addresses in `ALLOWED_ORIGINS` in `.env` (your own
  website), so other websites can't put your chatbot on their pages.
- **Rate limit and message length**: since anyone can send requests to a server directly
  (CORS only stops other *websites*), `api.py` also limits each visitor to 10 questions per minute
  and 1000 characters per question.
- **Error log**: everything that goes wrong on the server is written to `logs/server.log`.

## The web framework: FastAPI

A **web framework** is a library that does the general work of a web server for you: receiving
requests, finding the right function for each address, reading and checking the JSON, and sending
the response. Then you only write the part that is special to your project.

The chatbot server uses three packages that work together:

| Package | Its job | In the code |
|---|---|---|
| **FastAPI** | The web framework: connects each address to a Python function. | `@app.post("/chat/stream")` above the function `chat_stream` in `api.py` |
| **Pydantic** | Checks that the incoming JSON has the right fields and types, otherwise answers 422. | `class ChatRequest(BaseModel)` in `api.py` |
| **Uvicorn** | The server program that actually listens on port 8000 and passes the requests to FastAPI. | `uvicorn.run(app, ...)` at the bottom of `api.py` |

FastAPI also makes the test page at **http://127.0.0.1:8000/docs** automatically, from the code.

## Why not Django?

**Django** is the best-known Python web framework, and it's a good one. But it's built for a
different kind of job.

Django is "batteries included". It comes with:

- **templates**, to build HTML pages on the server,
- an **ORM**, to store data in an SQL database (like users, orders, signatures) using Python classes,
- an **admin site**, to edit that data in the browser,
- **user accounts** and logins, and forms.

The chatbot server needs **none** of these:

| Django gives you | Does the chatbot need it? |
|---|---|
| HTML pages built on the server | No. The page comes from the website (Django), and the chat panel draws itself with JavaScript. The chatbot server only sends data (JSON). |
| An SQL database and the ORM | No. The chatbot's data is a *vector database* (ChromaDB), which Django's ORM can't use. |
| Admin site, user accounts, forms | No. Visitors don't log in, and nothing is saved per visitor. |

What the chatbot server *does* need, FastAPI is made for:

- **An API with just a few endpoints.** In FastAPI that is one short file (`api.py`). Django would
  need a project, settings, a `urls.py`, views and an app folder before the first answer.
- **Streaming the answer word by word.** FastAPI has `StreamingResponse`, which works simply with a
  Python generator (a function that `yield`s the pieces).
- **Checking the incoming data**: done automatically from the Pydantic classes. In Django you
  write this checking yourself, or add an extra package (Django REST Framework).
- **The automatic test page** (`/docs`), useful for testing without the website.

In short: **Django is made for building whole websites with a database and users. FastAPI is made for small, fast
APIs that other programs talk to.** The chatbot server is the second kind.

(**Flask** is another small Python framework that would also work. FastAPI was chosen because it
checks the data and makes the `/docs` page automatically. With Flask you'd write both yourself.)

## The website does use Django

Django *is* the right choice for the **website** itself: it sends the pages (templates), and saves
the "Sign the Manifesto" signatures and newsletter sign-ups in a database (models, forms, the admin
site). That's exactly the kind of job it's made for. See [hi_website/README.md](../hi_website/README.md).

So the project uses each framework for what it's good at, **as two separate servers**:

- **Django runs the website, FastAPI runs the chatbot.** This is very common: the chat panel simply
  calls the chatbot's address. A slow AI answer (up to a minute) then never slows down the rest of
  the website, and either server can be restarted without the other.
- **Moving the chatbot into Django would also be possible**, because **only `api.py` uses FastAPI**.
  Everything in `core/` (the search, the AI, the citations) is plain Python and knows nothing
  about the web. A Django view would call the same `answer_question_stream(...)` and return
  a `StreamingHttpResponse` instead. That's not needed, so they stay separate.

This split is on purpose: the chatbot's "brain" (`core/`) is kept apart from how it is reached
(`api.py` for the website, `ask.py` for the terminal, `tests/run_tests.py` for the tests). All
three use the same `core/`.
