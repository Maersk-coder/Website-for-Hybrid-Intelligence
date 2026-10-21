# Hybrid Intelligence Chatbot

A chatbot that answers questions about AI and Hybrid Intelligence (collaboration between
humans and AI), including what is good and bad about AI. It answers **only** from a collection
of research papers, and says which paper and page each claim comes from.

It will be shown as a chat panel on Page 3 of the website.

> Work in progress, built in stages. Done so far: **Stage 1 (setup)**, **Stage 2 (reading the papers)**,
> **Stage 3 (answering questions in the terminal)**, **Stage 4 (the web API)** and **Stage 5 (the chat panel)**.

## How it works (RAG)

RAG means *retrieval-augmented generation*:

1. **Ingest (once):** the text of every paper is cut into small pieces ("chunks") and saved in a
   *vector database*. Each chunk is stored with an embedding (numbers that describe its meaning).
2. **Retrieve (every question):** the question is compared with all chunks, and the 6 closest
   in meaning are picked.
3. **Generate:** the question and those 6 chunks are sent to an AI model, which writes an
   answer using only those chunks, with sources. The AI model is either **Ollama** (free, on your
   own computer) or **Claude** (paid). See [Choosing the AI model](#choosing-the-ai-model-ollama-free-or-claude-paid).

## Important: the research papers are not in this repository

The PDF files are **not** uploaded to GitHub, because most research papers are protected by
copyright. The `papers/` folder is ignored by Git (see `.gitignore`), except for
[papers/README.md](papers/README.md), which **lists the papers used**. To run the chatbot
yourself, get those papers and put them in `papers/`.

The database (`data/`) is not uploaded either. It is built from the PDFs with `python ingest.py`.

## Files

| File / folder | What it is |
|---|---|
| `papers/` | Put the PDF research papers here. `papers/README.md` lists them. |
| `data/chroma/` | The vector database. Created automatically, not uploaded to GitHub. |
| `ingest.py` | Reads the PDFs, cleans the text, cuts it into chunks and saves them in the database. |
| `rag.py` | The "brain": finds the 6 best chunks for a question and asks the AI model (Ollama or Claude) to answer from them. The instructions for the AI (`SYSTEM_PROMPT`) are at the top. |
| `ask.py` | Ask questions in the terminal and see the answers and sources. |
| `api.py` | A small web server, so the website's chat panel can send questions and get answers. |
| `widget/chat-widget.js` | The chat panel for a website: builds it, sends questions to `api.py`, shows the answers word by word with numbered sources. |
| `widget/chat-widget.css` | The look of the chat panel (navy, with a soft glow). Loaded automatically by `chat-widget.js`. |
| `requirements.txt` | The Python packages the chatbot needs. |
| `.env.example` | Example of the secret settings file. Copy it to `.env` and fill it in. |
| `.gitignore` | Tells Git which files to leave out (secrets, database, papers). |

Coming in a later stage: test questions and deployment notes.

## Setup (once)

All commands are typed in a terminal (PowerShell) **inside the Chatbot folder**.
In VS Code: *Terminal → New Terminal*, then:

```powershell
cd Chatbot
```

### 1. Create a virtual environment

A virtual environment is a private box of Python packages for this project only, so it doesn't
mix with other Python projects on your computer.

```powershell
python -m venv .venv
```

This creates a `.venv` folder. Then switch it on:

```powershell
.\.venv\Scripts\Activate.ps1
```

You'll see `(.venv)` at the start of the line. **Switch it on every time you open a new terminal.**

> If you get an error that "running scripts is disabled", run this once, then try again:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 2. Install the packages

```powershell
pip install -r requirements.txt
```

This takes a few minutes (ChromaDB is big).

### 3. Create your settings file

```powershell
Copy-Item .env.example .env
```

`.env` holds your settings: which AI model answers the questions and, if you use Claude, your
secret API key. It is never uploaded to GitHub. Out of the box it is set to the free Ollama.

### 4. Install Ollama and download a model

See [Choosing the AI model](#choosing-the-ai-model-ollama-free-or-claude-paid) below.

## Building the index from the papers

### Check a PDF first (optional, recommended)

```powershell
python ingest.py --preview "name-of-paper.pdf"
```

Use the file name of a PDF in `papers/`, with the quotes. This shows a summary in the terminal
(the title found, the page where the reference list starts, how many chunks it makes and which
headers/footers were removed) and saves the full cleaned text in `preview.txt`. Open that file in
VS Code to read it. Each preview replaces the previous one. Nothing is added to the index.

### Build the index

```powershell
python ingest.py
```

- The first run downloads a small model (about 80 MB) that ChromaDB uses to make embeddings.
- Papers that are already in the index are skipped, so you can add new PDFs and run it again.
- At the end you get a summary, and a list of PDFs with little or no text. Those are probably
  scanned images and need OCR (text recognition) before the chatbot can use them.

### Start over

```powershell
python ingest.py --rebuild
```

Use this after changing a PDF, removing a PDF, or changing the settings at the top of `ingest.py`.

## Asking questions in the terminal

The AI model must be ready first: Ollama running with the model downloaded, or a Claude API key
in `.env` (see [Choosing the AI model](#choosing-the-ai-model-ollama-free-or-claude-paid)).

```powershell
python ask.py
```

Type a question after `You:` and press Enter. After a few seconds you get the answer and the list
of papers (and pages) it cites. Type `quit` to stop.

To see which excerpts the search found for each question (useful when an answer is poor):

```powershell
python ask.py --show-chunks
```

Each excerpt has a *distance*: lower means a closer match to the question.
If the right passage isn't in the list, the problem is the search, not the AI.

Follow-up questions work ("Why is that?"): the chatbot remembers the last 3 questions and answers.
Type `new` to start a fresh conversation.

## The web API (api.py)

The website can't run Python, so it talks to the chatbot through a small web server.

```powershell
python api.py
```

Leave this terminal open: the server runs until you press **Ctrl+C**. While it runs:

- **http://127.0.0.1:8000/health** - shows `"status": "ok"`, the number of chunks and the model in use.
- **http://127.0.0.1:8000/docs** - a test page made by FastAPI. Click **POST /chat** → **Try it out**,
  type a question in `"message"` and click **Execute**. The answer appears under *Response body*.

What it accepts and sends back:

```json
POST /chat
{
  "message": "Why is that?",
  "history": [
    {"role": "user", "content": "Do humans and AI perform better together?"},
    {"role": "assistant", "content": "On average, no ..."}
  ]
}

answer:
{
  "answer": "... [When combinations of humans and AI are useful: ..., p. 2] ...",
  "sources": [{"title": "...", "file_name": "...", "pages": ["1", "2"]}]
}
```

`history` is optional. The chat panel sends the earlier conversation there, so follow-ups work.

**`POST /chat/stream`** takes the same question, but sends the answer **piece by piece while it is
being written**, so the chat panel can show the first words after a few seconds instead of waiting
for the whole answer. The reply is one small JSON object per line:

```
{"type": "text", "text": "Hybrid"}
{"type": "text", "text": " Intelligence"}
...
{"type": "done", "answer": "<the full answer>", "sources": [...]}
```

If something goes wrong, the last line is `{"type": "error", "detail": "a friendly message"}`.
The full answer in the `done` line can differ slightly from the pieces, because citations are
repaired at the end. The chat panel shows the `done` version.

**Speed with Ollama:** the AI *reads* the excerpts in a few seconds, but *writes* only about
9 tokens per second on a laptop, so a whole answer takes 40-60 seconds. With `/chat/stream` the
first words appear after about 10 seconds. Fewer excerpts would not make it noticeably faster.

**Protection** (settings at the top of `api.py`):

| Setting | What it does |
|---|---|
| `MAX_MESSAGE_CHARS` | Questions longer than 1000 characters are refused. |
| `RATE_LIMIT`, `RATE_WINDOW_SECONDS` | Each visitor (IP address) can ask at most 10 questions per minute. |
| `ALLOWED_ORIGINS` (in `.env`) | Only these websites may use the server from a browser. Now: the VS Code Live Server addresses for testing. Later: your real domain. Note: this stops *other websites*, not people calling the server directly. The rate limit protects against that. |

Errors come back as `{"detail": "a friendly message"}`, with these codes: 400 (empty or too long),
422 (wrong format), 429 (too many questions), 503 (the AI or index isn't ready, e.g. Ollama not running), 500 (unexpected).

### Settings in rag.py

| Setting | What it does |
|---|---|
| `SYSTEM_PROMPT` | The instructions the AI follows for every answer. |
| `ANSWER_RULES` | Short extra rules sent next to each question: own words, about 150–250 words, only relevant excerpts, how to cite. |
| `NUMBER_OF_CHUNKS` | How many excerpts are sent with each question (6). |
| `OLLAMA_CONTEXT_SIZE` | Ollama only: how much text the model can read at once. Must fit the 6 excerpts. |
| `EFFORT` | Claude only: how carefully Claude thinks: `low`, `medium`, `high`, `xhigh`, `max`. Higher = better but slower and more expensive. |

## The chat panel (widget/)

A chat panel that can be put on any website with **one** `<script>` tag. On the Hybrid Intelligence
site it sits in the middle of Page 3.

```html
<div id="hi-chat" style="width: 720px; height: 600px"></div>
<script src="../Chatbot/widget/chat-widget.js" data-api="http://127.0.0.1:8000" data-target="#hi-chat"></script>
```

| Attribute | What it is |
|---|---|
| `src` | Where `chat-widget.js` is. `chat-widget.css` must be in the same folder. |
| `data-api` | The address of the chatbot server (`api.py`). Change it when the server moves online. |
| `data-target` | The box the panel goes in. The panel takes the box's width and height. |

What it does:

- **Start screen:** the headline, a short intro and example questions to click.
- **Conversation:** your questions on the right, answers on the left, written word by word while
  they arrive (it uses `/chat/stream`). Citations become small tags like `1 · p. 3`; the full
  paper titles are listed under **Sources**. **New chat** starts over.
- **Follow-up questions** work: the last messages are sent along.
- **While waiting:** "Reading the papers…" with pulsing dots.
- **Errors** (server not running, too many questions, ...) are shown as a message in the chat.
- **Phones:** the panel fills the screen width and gets more compact.
- **Mouse wheel:** over the panel it scrolls the chat; next to the panel it jumps between pages
  (see `Front Pages/General/JS/section_jump.js`).

Texts (headline, example questions, ...) are in `TEXTS` and `EXAMPLE_QUESTIONS` at the top of
`chat-widget.js`. Colors are at the top of `chat-widget.css`.

### Trying it on the website

Three things must run at the same time:

1. **Ollama** (it runs in the background after installing; check for the llama icon near the clock).
2. **The chatbot server**, in a terminal in the Chatbot folder: `python api.py` (leave it open).
3. **The website** with VS Code's **Live Server**: right-click `Front Pages/Front_Page.html` →
   *Open with Live Server*. Scroll to Page 3 and ask a question.

The website's address must be in `ALLOWED_ORIGINS` in `.env` (Live Server's
`http://127.0.0.1:5500` already is). Otherwise the browser blocks the chat and it says it can't reach the chatbot.
(In the `api.py` terminal you then see `OPTIONS /chat/stream ... 400 Bad Request`.)

Opening `Front_Page.html` by double-clicking also works if `ALLOWED_ORIGINS` ends with `,null`
(a double-clicked file introduces itself as "null"). Only use that on your own computer, and remove
it before the website goes online. After changing `.env`, restart `api.py` (Ctrl+C, then `python api.py`).

## Choosing the AI model: Ollama (free) or Claude (paid)

The chatbot can use two kinds of AI model to write the answers. Searching the papers works the
same with both. Only the step that *writes* the answer changes.

| | **Ollama** (current setting) | **Claude** (Anthropic) |
|---|---|---|
| Cost | Free | Paid per question (see below) |
| Where it runs | On your own computer | On Anthropic's servers |
| Answer quality | OK. Small models sometimes cite less exactly or miss nuance. | Very good, careful citations and balanced answers |
| Speed | Depends on your computer (seconds to a minute) | A few seconds |
| On a public website | Only while your own computer is on and running it | Works anywhere |

You switch between them with **one line in `.env`**: `LLM_PROVIDER=ollama` or `LLM_PROVIDER=anthropic`.
No code changes are needed.

### Using Ollama (free)

1. Download and install Ollama from [ollama.com/download](https://ollama.com/download) (Windows version).
   After installing, Ollama runs in the background (a small llama icon near the clock).
2. Open a **new** terminal and download the model (about 3.5 GB, once):
   ```powershell
   ollama pull qwen3.5:4b
   ```
3. Check that `.env` contains:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=qwen3.5:4b
   OLLAMA_THINK=false
   ```
4. Run `python ask.py` as usual.

**Other models:** any model from [ollama.com/library](https://ollama.com/library) can be used.
Download it with `ollama pull <name>` and put the name in `OLLAMA_MODEL`. Bigger models give
better answers but need more memory and are slower. On a laptop with 16 GB of memory and a 4 GB
graphics card:

| `OLLAMA_MODEL` | Download | Notes |
|---|---|---|
| `qwen3.5:4b` | ~3.5 GB | **Used now.** Faster. With the 8,192-token reading limit it runs about half on the graphics card, half on the processor (`ollama ps` shows this). |
| `qwen3.5:9b` | ~7 GB | Strongest that fits. Slower: part of it runs on the processor. |
| `gemma3:4b` | ~3.4 GB | Fast. Can't think step by step (keep `OLLAMA_THINK=false`). |

`ollama list` shows the models you have downloaded. `ollama rm <name>` deletes one to free disk space.

**Thinking (`OLLAMA_THINK`):** Qwen models can reason step by step before they answer. Set
`OLLAMA_THINK=true` to try it. Answers may get better, but each one can take minutes on a laptop.

### Switching to Claude (paid)

1. Create an account at [console.anthropic.com](https://console.anthropic.com) and add credit
   (*Billing*). Optional but recommended: set a monthly spending limit (*Limits*).
2. Create an API key (*API Keys*) and copy it.
3. In `.env`, change these lines:
   ```
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=<paste your key here>
   ANTHROPIC_MODEL=claude-opus-5-5
   ```
4. Run `python ask.py` as usual. To go back to Ollama, set `LLM_PROVIDER=ollama` again.

Approximate cost per question with the Claude models (6 excerpts + one answer):

| `ANTHROPIC_MODEL` | Cost per question | Questions per $1 |
|---|---|---|
| `claude-opus-5-5` (best) | ~5 cents | ~20 |
| `claude-sonnet-5-5` | ~2 cents | ~50 |
| `claude-haiku-5-5` (cheapest) | ~0.1 cent | ~1,000 |

Using the API key is paid whether the website is published or not: every question sent to
Claude is billed to the key's account. A claude.ai subscription (Pro/Max) does not include API use.

## How the text is cleaned (ingest.py)

- **Headers and footers:** text at the top or bottom of the page that repeats on many pages
  (like a journal name) is removed. So are lines that are only a page number.
- **Title page part:** if an "Abstract" or "Introduction" heading is found on the first 3 pages,
  everything before it (title, author names, addresses, dates) is skipped. The title is saved
  separately. If there is no such heading, nothing is skipped.
- **Broken words:** `collab-` + `oration` at a line break becomes `collaboration`.
- **References:** everything from the "References" / "Bibliography" heading onwards is skipped.
  (Appendices after the references are skipped too.)
- **Title:** taken from the PDF's hidden information, otherwise the biggest text on page 1,
  otherwise the file name.
- **Chunks:** 300–500 words, built from whole paragraphs where possible, and each chunk starts
  with the last 50 words of the one before. Each chunk is saved with the paper title,
  file name, page number(s) and a chunk id.

## Good to know

- **OneDrive:** this folder is synced by OneDrive. If you see "file in use" or "permission
  denied" errors, pause OneDrive syncing while you run the scripts.
