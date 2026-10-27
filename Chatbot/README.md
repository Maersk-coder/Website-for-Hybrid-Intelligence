# Hybrid Intelligence Chatbot

A chatbot that answers questions about AI and Hybrid Intelligence (collaboration between
humans and AI), including what is good and bad about AI. It answers **only** from a collection
of research papers, and says which paper and page each claim comes from.

It is shown as a chat panel in the middle of Page 3 of the website. The answers are written by a
free AI model (**Ollama**) running on your own computer.

> Built in 6 stages: **1** setup, **2** reading the papers, **3** answering questions in the terminal,
> **4** the web API, **5** the chat panel, **6** test questions and going online
> (see [Testing answer quality](#testing-answer-quality) and [DEPLOYMENT.md](DEPLOYMENT.md)).
>
> How the chat panel (client) and the Python server talk to each other, and why the server uses
> FastAPI and not Django: see [SERVER_AND_CLIENT.md](SERVER_AND_CLIENT.md).

## How it works (RAG)

RAG means *retrieval-augmented generation*:

1. **Ingest (once):** the text of every paper is cut into pieces ("chunks") and saved in a
   *vector database*. Each chunk is stored with an embedding (numbers that describe its meaning).
2. **Retrieve (every question):** the question is compared with all chunks, and the 8 closest
   in meaning are picked.
3. **Generate:** the question and those 8 chunks are sent to the AI model, which writes an
   answer using only those chunks, with sources.

## Important: the research papers are not in this repository

The PDF files are **not** uploaded to GitHub, because most research papers are protected by
copyright. The `papers/` folder is ignored by Git (see `.gitignore`), except for
[papers/README.md](papers/README.md), which **lists the papers used**. To run the chatbot
yourself, get those papers and put them in `papers/`.

The database (`data/`) is not uploaded either. It is built from the PDFs with `python ingest.py`.

## The folder

The files you **run** are at the top. The machinery they use is in `core/`, one file per job.

```
Chatbot/
├── ingest.py          RUN: build the search index from the PDFs
├── ask.py             RUN: ask questions in the terminal (for testing)
├── api.py             RUN: the web server the website's chat panel talks to
├── check.py           RUN: check that everything is ready, and say what to fix
├── settings.py        ALL settings and texts in one place
│
├── core/              the machinery (you don't run these)
│   ├── errors.py         ChatbotError: a problem with a friendly message
│   ├── pdf_text.py       read a PDF, clean its text, find its title
│   ├── chunks.py         cut the text into chunks
│   ├── embeddings.py     turn text into numbers for searching (Ollama: nomic-embed-text)
│   ├── keywords.py       the word search: excerpts with the question's rare words
│   ├── database.py       the search index: store chunks, find the best matches
│   ├── ai_model.py       talk to Ollama
│   └── answers.py        answer a question: search, ask the AI, repair citations, list sources
│
├── widget/            the chat panel for the website (chat-widget.js + chat-widget.css)
├── tests/             test questions (test_questions.md), the script that runs them
│                      (run_tests.py) and its reports (results/)
├── papers/            your PDFs, in subfolders if you like (e.g. "Pro AI/", "Hybrid Intelligence/"),
│                      + README.md (the list of papers) and titles.txt (titles you set yourself)
├── data/              made automatically: the search index (chroma/) and preview.txt
├── logs/              made automatically: server.log, the problems api.py ran into
│
├── DEPLOYMENT.md      how to put the website and the chatbot online
├── .env               your own settings (made from .env.example)
├── .env.example       an example of .env
├── requirements.txt   the Python packages needed
└── .gitignore         the files Git leaves out (settings, database, papers, logs)
```

### Where to look when something goes wrong

**Start with `python check.py`.** It checks the packages, the settings, the PDFs, the index,
Ollama, the model and the server, and says what to fix.

| What you see | Where to look |
|---|---|
| "Could not reach Ollama" | Ollama isn't running (or is updating itself): look for the llama icon near the clock. Code: `core/ai_model.py` |
| The chat says it can't reach the chatbot | `api.py` isn't running, or the website's address isn't in `ALLOWED_ORIGINS` in `.env` |
| Strange text, headers left in, wrong paper title | `core/pdf_text.py`. Check the PDF with `python ingest.py --preview "file.pdf"` |
| The search finds the wrong excerpts | `core/database.py` / `core/chunks.py` / `core/embeddings.py` / `core/keywords.py`. Check with `python ask.py --show-chunks` |
| "The index was built with another embedding model" | `EMBEDDING_MODEL` in `settings.py` was changed: run `python ingest.py --rebuild` |
| Answers are too long, copy the papers, or ignore the rules | `SYSTEM_PROMPT` and `ANSWER_RULES` in `settings.py` |
| A real question gets "That's not something I can help with..." | `OFF_TOPIC_DISTANCE` in `settings.py` is too low for that question. Check its distance with `python ask.py --show-chunks` |
| Citations or the Sources list look wrong | `core/answers.py` (`fix_citations`, `find_sources`, `add_missing_citations`) |
| "What are the sources?" gets the wrong kind of reply | `core/answers.py` (`asks_for_sources`, `sources_of_previous_answer`) |
| Something went wrong while the server was running | `logs/server.log`: each problem with the date and time |
| The chat panel looks or behaves wrong | `widget/chat-widget.js` / `widget/chat-widget.css` |

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

`.env` holds your own settings: which Ollama model writes the answers, and which websites may use
the chatbot. It is never uploaded to GitHub.

### 4. Install Ollama and download the two models

1. Download and install Ollama from [ollama.com/download](https://ollama.com/download) (Windows version).
   After installing, Ollama runs in the background (a small llama icon near the clock).
2. Open a **new** terminal and download the two models (once):
   ```powershell
   ollama pull qwen3.5:4b
   ollama pull nomic-embed-text
   ```
   `qwen3.5:4b` (about 3.5 GB) writes the answers. `nomic-embed-text` (about 270 MB) turns text into
   numbers for the search (see [How the search works](#how-the-search-works)).

### 5. Check

```powershell
python check.py
```

## Building the index from the papers

### Check a PDF first (optional, recommended)

```powershell
python ingest.py --preview "name-of-paper.pdf"
```

Use the file name of a PDF in `papers/`, with the quotes. This shows a summary in the terminal
(the title found, where the text starts, where the reference list starts, how many chunks it makes
and which headers/footers were removed) and saves the full cleaned text in `data/preview.txt`.
Open that file in VS Code to read it. Each preview replaces the previous one. Nothing is added to the index.

### A wrong title? Set it yourself

The title is found automatically, but that sometimes fails, for example with a cover page where all
the text is the same size. Then add a line to **`papers/titles.txt`**:

```
The simple macroecnoomics of AI.pdf = The Simple Macroeconomics of AI
```

Only the file name, without its folder. Then rebuild the index (`python ingest.py --rebuild`).

### Build the index

```powershell
python ingest.py
```

PDFs in subfolders of `papers/` are found too. Each paper is stored with its folder in its name
(e.g. `Pro AI/Generative AI at Work.pdf`). After moving PDFs to another folder, rebuild the index.

- Ollama must be running: it makes the embeddings (about 2 minutes for 7 papers on a laptop).
- Papers that are already in the index are skipped, so you can add new PDFs and run it again.
- At the end you get a summary, and a list of PDFs with little or no text. Those are probably
  scanned images and need OCR (text recognition) before the chatbot can use them.

### Start over

```powershell
python ingest.py --rebuild
```

Use this after changing or removing a PDF, or after changing the chunk or PDF settings in `settings.py`.

## Asking questions in the terminal

Ollama must be running, with the model downloaded.

```powershell
python ask.py
```

Type a question after `You:` and press Enter. After a while you get the answer and the list
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

The website can't run Python, so it talks to the chatbot through a small web server, built with
FastAPI (why FastAPI and how the two sides talk: [SERVER_AND_CLIENT.md](SERVER_AND_CLIENT.md)).

```powershell
python api.py
```

Leave this terminal open: the server runs until you press **Ctrl+C**. While it runs:

- **http://127.0.0.1:8000/health** - shows `"status": "ok"`, the number of chunks and the model in use.
- **http://127.0.0.1:8000/docs** - a test page made by FastAPI. Click **POST /chat** → **Try it out**,
  change the question in `"message"` if you like, and click **Execute**. The answer appears under *Response body*.

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

**Speed:** the AI *reads* the excerpts in a few seconds, but *writes* only about 9 tokens per second
on a laptop, so a whole answer takes 40-60 seconds. With `/chat/stream` the first words appear after
about 10 seconds (about 25 seconds for the first question, while Ollama loads the model).

**Protection** (settings in `settings.py` and `.env`):

| Setting | What it does |
|---|---|
| `MAX_MESSAGE_CHARS` | Questions longer than 1000 characters are refused. |
| `RATE_LIMIT`, `RATE_WINDOW_SECONDS` | Each visitor (IP address) can ask at most 10 questions per minute. |
| `ALLOWED_ORIGINS` (in `.env`) | Only these websites may use the server from a browser. Now: the VS Code Live Server addresses for testing. Later: your real domain. Note: this stops *other websites*, not people calling the server directly. The rate limit protects against that. |

Errors come back as `{"detail": "a friendly message"}`, with these codes: 400 (empty or too long),
422 (wrong format), 429 (too many questions), 503 (the AI or index isn't ready, e.g. Ollama not running), 500 (unexpected).

**The error log:** problems are also written to `logs/server.log`, with the date and time: when
Ollama couldn't be reached, when someone asked too many questions, and the full details of any
unexpected error. The file stays small: at 1 MB a new one is started (the 3 newest old ones are kept).

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

## Testing answer quality

[tests/test_questions.md](tests/test_questions.md) holds test questions of different kinds:
definitions, benefits and risks, specific facts, a follow-up, a tricky question with a wrong
assumption, and one the papers don't cover. For each it notes what a good answer contains, with
page numbers. There are empty slots for questions about papers you add later.

```powershell
python tests/run_tests.py              all questions (about 10-20 minutes on a laptop)
python tests/run_tests.py --only 3,6   only some questions
```

It asks the chatbot every question and saves a report in `tests/results/`, named after the date
and time. For each question the report shows the answer, the sources, the excerpts the search
found, the time it took, and three automatic checks:

| Check | Means |
|---|---|
| **Search** | The search found the paper(s) a good answer needs. If not: the problem is the search (chunks, `NUMBER_OF_CHUNKS`). |
| **Cited** | The answer cites those papers. If the search found them but the answer doesn't cite them: the problem is the AI or the prompt. |
| **Not covered** | It said "the papers don't cover this" exactly when it should. |

At the bottom of each question there's room for **your score (1-5)** and notes: the automatic
checks can't tell whether an answer is actually *good*. Compare reports from before and after a
change (the prompt in `settings.py`, the chunk sizes, the model) to see whether answers got better.

## Going online

See **[DEPLOYMENT.md](DEPLOYMENT.md)**: the website on GitHub Pages (free), and three routes for
the chatbot server, with step-by-step instructions for running it from your own laptop through a
free Cloudflare tunnel.

## Settings

**`settings.py`** holds all the settings and texts. The most useful ones:

| Setting | What it does |
|---|---|
| `SYSTEM_PROMPT` | The instructions the AI follows for every answer. |
| `ANSWER_RULES` | Short extra rules sent next to each question: everyday words, 4–6 sentences (1–2 for facts), only relevant excerpts, how to cite, and a 1–2 sentence reply when the papers don't cover the question. |
| `NUMBER_OF_CHUNKS` | How many excerpts are sent with each question (8). |
| `MAX_CHUNKS_PER_PAPER`, `SEARCH_CANDIDATES` | At most 3 of those excerpts come from the same paper, so long papers can't crowd out the others (the search picks them from the best 25 matches). |
| `EMBEDDING_MODEL` | The Ollama model that makes the embeddings for searching (`nomic-embed-text`). Rebuild the index after changing it. |
| `OFF_TOPIC_DISTANCE`, `WORD_MATCH_FOR_TOPIC`, `OFF_TOPIC_ANSWER` | Questions that have nothing to do with the papers (pizza, weather, ...) get `OFF_TOPIC_ANSWER` straight away, without asking the AI. A question counts as off-topic when even the best excerpt has a distance above 0.77 **and** no excerpt contains at least 75% of the question's important words (see [How the search works](#how-the-search-works)). |
| `CHUNK_MIN_WORDS`, `CHUNK_MAX_WORDS`, `OVERLAP_WORDS` | The size of the chunks (250–400 words, 50 words overlap). Rebuild the index after changing them. |
| `OLLAMA_CONTEXT_SIZE` | How much text the model can read at once. Must fit the excerpts and the conversation. |
| `MAX_HISTORY_MESSAGES` | How many earlier messages the AI sees (6 = the last 3 questions and answers). |

**`.env`** holds the settings that differ per computer:

| Setting | What it does |
|---|---|
| `OLLAMA_MODEL` | Which Ollama model writes the answers (now `qwen3.5:4b`). |
| `OLLAMA_URL` | Where Ollama runs (normally `http://localhost:11434`). |
| `OLLAMA_THINK` | `true` = the model reasons step by step first. Can give better answers, but much slower. |
| `ALLOWED_ORIGINS` | The websites allowed to use the chatbot. |

### Other Ollama models

Any model from [ollama.com/library](https://ollama.com/library) can be used. Download it with
`ollama pull <name>` and put the name in `OLLAMA_MODEL` in `.env`. Bigger models give better answers
but need more memory and are slower. On a laptop with 16 GB of memory and a 4 GB graphics card:

| `OLLAMA_MODEL` | Download | Notes |
|---|---|---|
| `qwen3.5:4b` | ~3.5 GB | **Used now.** With the 8,192-token reading limit it runs about half on the graphics card, half on the processor (`ollama ps` shows this). |
| `qwen3.5:9b` | ~7 GB | Stronger, but slower: more of it runs on the processor. |

`ollama list` shows the models you have downloaded. `ollama rm <name>` deletes one to free disk space.

### Switching to a paid model later (Claude)

The chatbot used to have the option to let Claude (Anthropic's paid AI model) write the answers
instead of Ollama: better and faster answers, but paid per question. It was removed to keep the
code simple. That version is saved in Git, in commit **`0145a3c`**: see `rag.py` there
(the functions `ask_claude` and `stream_ai`), and the "Choosing the AI model" part of its README.

## How the text is cleaned (core/pdf_text.py)

- **Headers and footers:** text at the top or bottom of the page that repeats on many pages
  (like a journal name) is removed. So are lines that are only a page number.
- **Title page part:** if an "Abstract" or "Introduction" heading is found on the first 3 pages,
  everything before it (title, author names, addresses, dates) is skipped. The title is saved
  separately. If there is no such heading, nothing is skipped.
- **Broken words:** `collab-` + `oration` at a line break becomes `collaboration`.
- **References:** everything from the "References" / "Bibliography" heading onwards is skipped
  (appendices after the references too). The heading only counts after the first 30% of the pages
  (`REFERENCES_FROM_SHARE`), so one in a table of contents is ignored.
- **Title:** taken from `papers/titles.txt` if it's there, otherwise the PDF's hidden information
  (unless it's a placeholder like "Paper draft"), otherwise the biggest text on page 1, otherwise
  the file name.
- **Chunks** (`core/chunks.py`): 250–400 words, built from whole paragraphs where possible, and each
  chunk starts with the last 50 words of the one before. Each chunk is saved with the paper title,
  file name (with its folder), page number(s) and a chunk id.

## How the search works

Each chunk, and each question, is turned into an **embedding**: a list of 768 numbers that captures
what the text is about. Texts about similar things get similar numbers. The search compares the
question's numbers with every chunk's, and the closest chunks are the best matches (the *distance*
shown by `python ask.py --show-chunks`: lower = closer).

The embeddings are made by **`nomic-embed-text`**, a model that runs in Ollama (`core/embeddings.py`).
It reads the whole chunk. (Until October 2026 the chatbot used ChromaDB's standard model, which only
read the first ~190 words of each chunk, so most of each chunk was invisible to the search.)

### The word search

The meaning search is good at everyday language, but weak at rare special terms ("stochastic
parrot", "AMIE", "Moravec paradox"). So a **word search** (`core/keywords.py`) runs next to it:
it finds the excerpts that contain the question's words, where **rare words count a lot** ("parrot"
is in only a few excerpts) and common words count very little ("human" is in hundreds). The two
rankings are combined: an excerpt near the top of either one moves up.

### Picking the 8 excerpts

From the combined ranking, 8 excerpts are picked, with at most 3 from the same paper. If the best
places are all taken by a few papers, the search looks again in the **other** papers, so one long
paper can't crowd out the others and the AI sees several points of view.

### Citations: the safety net

The AI is told to cite every claim, but a small model sometimes forgets. When an answer cites
nothing at all, `add_missing_citations` (in `core/answers.py`) does it: for each sentence it finds
the excerpt the sentence is closest to in meaning, and adds that excerpt's citation. A sentence
that isn't clearly close to any excerpt (distance above `CITE_DISTANCE`, 0.45) gets none, rather
than a wrong one. Answers saying the papers don't cover the question are left alone.

### "What are the sources for this claim?"

A short question about the previous answer's sources ("What are the sources for this claim?",
"Where does that come from?", "Which study found that?", "Sources?") gets a direct reply listing
the papers and pages the previous answer cited, without a new search. A new question that just
contains the word "sources" ("What are the sources of bias in AI?") is treated as a normal question.

### Off-topic questions

A question gets the fixed `OFF_TOPIC_ANSWER` (without asking the AI) only when **both** are true:
- even the closest excerpt is far away in meaning (distance above `OFF_TOPIC_DISTANCE`, 0.77), and
- no excerpt contains most of the question's important words (less than `WORD_MATCH_FOR_TOPIC`, 75%).

"What is the best pizza in Rome?" is far away and "pizza" is in no paper: off-topic. "What is a
stochastic parrot?" is also far away in meaning, but "stochastic" and "parrot" are both in the
papers: it goes to the AI. After adding papers, restart `api.py` so the word search includes them.

## Good to know

- **OneDrive:** this folder is synced by OneDrive. If you see "file in use" or "permission
  denied" errors, pause OneDrive syncing while you run the scripts.
- **Ollama updates itself** now and then. While it updates (a few minutes) it is switched off, and
  the chat says it can't reach Ollama. `python check.py` tells you when it's back.
