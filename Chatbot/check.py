"""
check.py - checks that everything the chatbot needs is ready, and says what to fix.

How to run it (inside the Chatbot folder, with the virtual environment on):
  python check.py

It checks, in order:
  1. the Python packages        4. the search index
  2. the .env settings file     5. Ollama and the AI model
  3. the PDFs in papers/        6. the chatbot server (api.py)

Each line starts with:
  [ OK ]  fine
  [FAIL]  must be fixed before the chatbot works (the line below says how)
  [NOTE]  worth knowing, but the chatbot can still work
"""

import importlib
import sys
from pathlib import Path

HERE = Path(__file__).parent
problems = 0


def ok(text):
    print(f"[ OK ]  {text}")


def fail(text, fix):
    global problems
    problems += 1
    print(f"[FAIL]  {text}")
    print(f"        -> {fix}")


def note(text):
    print(f"[NOTE]  {text}")


def check_packages():
    """1. Are the Python packages installed? Without them nothing else can be checked."""
    missing = []
    for package in ("pymupdf", "chromadb", "ollama", "httpx", "fastapi", "uvicorn", "dotenv"):
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)
    if missing:
        fail(f"Python packages missing: {', '.join(missing)}",
             "Switch on the virtual environment (.\\.venv\\Scripts\\Activate.ps1), then: pip install -r requirements.txt")
        return False
    ok("Python packages are installed")
    return True


def check_env():
    """2. Is there a .env file, and what does it say?"""
    from settings import ALLOWED_ORIGINS, OLLAMA_MODEL

    if (HERE / ".env").exists():
        ok(".env settings file found")
    else:
        note(".env not found, so the standard settings are used. To make one: Copy-Item .env.example .env")
    if ALLOWED_ORIGINS:
        ok(f"Allowed websites: {', '.join(ALLOWED_ORIGINS)}")
    else:
        fail("No allowed websites (ALLOWED_ORIGINS is empty), so the website can't use the chatbot",
             "Add ALLOWED_ORIGINS=http://127.0.0.1:5500 to .env")
    if "null" in ALLOWED_ORIGINS:
        note("ALLOWED_ORIGINS includes 'null' (for double-clicking Front_Page.html). Remove it before going online.")
    note(f"AI model in use: {OLLAMA_MODEL}")


def check_papers_and_index():
    """3 + 4. Are there PDFs, and are they all in the search index?"""
    from settings import COLLECTION_NAME, PAPERS_FOLDER

    pdfs = sorted(path.name for path in PAPERS_FOLDER.glob("*.pdf"))
    if pdfs:
        ok(f"{len(pdfs)} PDF(s) in papers/")
    else:
        fail("No PDFs in papers/", "Put your research papers (PDF files) in the papers folder")

    from core.database import open_database
    collection = open_database().get_or_create_collection(name=COLLECTION_NAME)
    count = collection.count()
    if count == 0:
        fail("The search index is empty", "Run: python ingest.py")
        return

    indexed = {info["file_name"] for info in collection.get(include=["metadatas"])["metadatas"]}
    ok(f"Search index has {count} chunks from {len(indexed)} paper(s)")

    not_indexed = [name for name in pdfs if name not in indexed]
    gone = sorted(indexed - set(pdfs))
    if not_indexed:
        fail(f"PDFs not in the index yet: {', '.join(not_indexed)}", "Run: python ingest.py")
    if gone:
        note(f"In the index, but the PDF is no longer in papers/: {', '.join(gone)}. "
             "To remove it from the index: python ingest.py --rebuild")


def check_ollama():
    """5. Is Ollama running, and is the model downloaded?"""
    import httpx
    from settings import OLLAMA_MODEL, OLLAMA_URL

    try:
        version = httpx.get(f"{OLLAMA_URL}/api/version", timeout=3).json()["version"]
    except Exception:
        fail("Ollama is not running (or is busy updating itself)",
             "Look for the llama icon near the clock. If it's not there: Windows key, type Ollama, press Enter")
        return
    ok(f"Ollama is running (version {version})")

    models = [model["name"] for model in httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5).json().get("models", [])]
    if OLLAMA_MODEL in models or f"{OLLAMA_MODEL}:latest" in models:
        ok(f"Model {OLLAMA_MODEL} is downloaded")
    else:
        fail(f"Model {OLLAMA_MODEL} is not downloaded", f"Run: ollama pull {OLLAMA_MODEL}")


def check_server():
    """6. Is the chatbot server (api.py) running? Needed for the website, not for ask.py."""
    import httpx
    from settings import SERVER_HOST, SERVER_PORT

    try:
        reply = httpx.get(f"http://{SERVER_HOST}:{SERVER_PORT}/health", timeout=3).json()
    except Exception:
        note("The chatbot server (api.py) is not running. The website needs it: python api.py")
        return
    if reply.get("status") == "ok":
        ok(f"The chatbot server is running ({reply.get('model')})")
    else:
        fail(f"The chatbot server is running, but reports a problem: {reply.get('detail')}",
             "Fix the problem above, then restart the server (Ctrl+C, then python api.py)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Checking the chatbot...\n")

    if check_packages():
        check_env()
        check_papers_and_index()
        check_ollama()
        check_server()

    print()
    if problems:
        print(f"{problems} problem(s) to fix (see the [FAIL] lines above).")
    else:
        print("All good: the chatbot is ready.")
