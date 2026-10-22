"""
core/answers.py - answer one question. This is the "brain" that ties the other parts together:

  1. Search: find the chunks that best match the question (core/database.py)
  2. Ask: send the question and those chunks to the AI model (core/ai_model.py)
  3. Tidy up: repair citations the model wrote wrongly, and list the sources it cited

Look here when: citations or the Sources list look wrong, or follow-up questions misbehave.
(The texts the AI gets, SYSTEM_PROMPT and ANSWER_RULES, are in settings.py.)
"""

import re

from core.ai_model import stream_answer
from core.database import page_label, retrieve
from settings import ANSWER_RULES, MAX_HISTORY_CHARS, MAX_HISTORY_MESSAGES


# ---------------------------------------------------------------------------
# Before asking: the conversation and the message
# ---------------------------------------------------------------------------

def clean_history(history):
    """Keep only the last few messages of the conversation, in a safe shape.

    history is a list like [{"role": "user", "content": "..."}, {"role": "assistant", ...}].
    Messages with an unknown role or no text are dropped, long ones are shortened,
    and the list always starts with a question (the AI model expects that).
    """
    cleaned = []
    for message in history or []:
        role = message.get("role")
        content = str(message.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            cleaned.append({"role": role, "content": content[:MAX_HISTORY_CHARS]})

    cleaned = cleaned[-MAX_HISTORY_MESSAGES:]
    while cleaned and cleaned[0]["role"] != "user":
        cleaned.pop(0)
    return cleaned


def search_text(question, history):
    """The text used to search the papers.

    A follow-up like "tell me more about that" means nothing on its own,
    so the previous question is searched together with it.
    """
    earlier_questions = [message["content"] for message in history if message["role"] == "user"]
    if earlier_questions:
        return earlier_questions[-1] + "\n" + question
    return question


def build_message(question, chunks):
    """Put the excerpts and the question together into the message for the AI model."""
    parts = ["Research excerpts:\n"]
    for chunk in chunks:
        parts.append(
            "---\n"
            f"Title: {chunk['title']}\n"
            f"Page: {page_label(chunk)}\n"
            f"{chunk['text']}\n"
        )
    # A real example citation, made from the first excerpt.
    example = f"[{chunks[0]['title']}, p. {page_label(chunks[0])}]"
    parts.append(ANSWER_RULES.format(example=example) + "\n\n" + f"Question: {question}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# After asking: citations and sources
# ---------------------------------------------------------------------------

def fix_citations(answer, chunks):
    """Repair citations that small models sometimes write wrongly.

      "[Excerpt 2, p. 4]"                       -> "[Hybrid Intelligence, p. 4]"
      "[Paper title: Hybrid Intelligence, p. 4]" -> "[Hybrid Intelligence, p. 4]"
    """
    # re.sub calls this small function for every "Excerpt N" it finds, and puts in
    # whatever it returns. match.group(1) is the N, match.group(0) the whole "Excerpt N".
    def to_title(match):
        number = int(match.group(1))
        if 1 <= number <= len(chunks):
            return chunks[number - 1]["title"]
        return match.group(0)  # a number we don't know: leave it as it is

    # "Excerpt 2" only when ", p." or ", pp." comes right after it ((?=...) = "followed by").
    answer = re.sub(r"\bExcerpt\s+(\d+)(?=,\s*pp?\.)", to_title, answer)
    # "[Paper title: " or "[Title: " at the start of a citation becomes just "[".
    answer = re.sub(r"\[\s*(Paper\s+)?title:\s*", "[", answer, flags=re.IGNORECASE)
    return answer


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
        # re.escape makes signs in the title (like ? or :) count as normal letters.
        # The group ( ) catches the page numbers: digits, dashes, commas and spaces, ending with a digit.
        pattern = re.escape(title) + r",\s*pp?\.\s*([\d\-–, ]+\d)"
        pages = []
        for found in re.findall(pattern, answer):
            for page in found.split(","):
                page = page.strip()  # remove spaces around the number
                if page and page not in pages:
                    pages.append(page)
        if pages:
            # Sort by the first number, then shortest first: "2", "5", "5-6", "7"
            # (key = what to sort by; lambda is a tiny one-line function that works it out per page)
            pages.sort(key=lambda page: (int(re.match(r"\d+", page).group()), len(page)))
            sources.append({"title": title, "file_name": chunk["file_name"], "pages": pages})
    return sources


# ---------------------------------------------------------------------------
# The whole thing
# ---------------------------------------------------------------------------

def answer_question_stream(question, history=None):
    """Answer one question, giving the answer piece by piece while it is written.

    history (optional) is the earlier conversation:
      [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    Only the plain questions and answers are kept there, not the excerpts.

    Gives back:
      ("text", "a few words")  for each new piece of the answer, and at the very end
      ("done", {...})          a dictionary with:
          answer  - the full answer, with citations repaired
          sources - the papers (and pages) cited in the answer
          chunks  - the excerpts that were retrieved (for checking with --show-chunks)
    """
    history = clean_history(history)
    chunks = retrieve(search_text(question, history))

    # Like stream_answer, this is a generator: each "yield" hands a piece on straight away
    # (to api.py, which sends it to the chat panel), while the pieces are also kept to
    # put the whole answer together at the end.
    pieces = []
    for piece in stream_answer(build_message(question, chunks), history):
        pieces.append(piece)
        yield "text", piece

    answer = "".join(pieces)
    # Some models write out their thinking between <think> tags first. Remove it.
    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()
    answer = fix_citations(answer, chunks)
    yield "done", {"answer": answer, "sources": find_sources(answer, chunks), "chunks": chunks}


def answer_question(question, history=None):
    """Answer one question and give back the whole answer at once (used by ask.py and /chat).

    Returns the same dictionary as the "done" step of answer_question_stream.
    """
    # Run through all the pieces without showing them, and keep only the final "done" step.
    for kind, data in answer_question_stream(question, history):
        if kind == "done":
            return data
