# Hybrid Intelligence Chatbot

A chatbot that answers questions about AI and Hybrid Intelligence (collaboration between
humans and AI), including what is good and bad about AI. It answers **only** from a collection
of research papers, and says which paper and page each claim comes from.

It will be shown as a chat panel on Page 3 of the website.

> Work in progress, built in stages. Done so far: **Stage 1 (setup)**, **Stage 2 (reading the papers)**
> and **Stage 3 (answering questions in the terminal)**.

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
| `requirements.txt` | The Python packages the chatbot needs. |
| `.env.example` | Example of the secret settings file. Copy it to `.env` and fill it in. |
| `.gitignore` | Tells Git which files to leave out (secrets, database, papers). |

Coming in later stages: `api.py` (web server) and `widget/` (the chat panel for the website).

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
If the right passage isn't in the list, the problem is the search, not Claude.

### Settings in rag.py

| Setting | What it does |
|---|---|
| `SYSTEM_PROMPT` | The instructions the AI follows for every answer. |
| `ANSWER_RULES` | Short extra rules sent next to each question: own words, about 150–250 words, only relevant excerpts, how to cite. |
| `NUMBER_OF_CHUNKS` | How many excerpts are sent with each question (6). |
| `OLLAMA_CONTEXT_SIZE` | Ollama only: how much text the model can read at once. Must fit the 6 excerpts. |
| `EFFORT` | Claude only: how carefully Claude thinks: `low`, `medium`, `high`, `xhigh`, `max`. Higher = better but slower and more expensive. |

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
2. Open a **new** terminal and download the model (about 3 GB, once):
   ```powershell
   ollama pull gemma3:4b
   ```
3. Check that `.env` contains:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=gemma3:4b
   ```
4. Run `python ask.py` as usual.

**Other models:** any model from [ollama.com/library](https://ollama.com/library) can be used.
Download it with `ollama pull <name>` and put the name in `OLLAMA_MODEL`. Bigger models give
better answers but need more memory and are slower. `gemma3:4b` fits a laptop with 16 GB of memory
and a 4 GB graphics card. With more memory, try a model around 8 billion parameters (e.g. names
ending in `:8b`).

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
