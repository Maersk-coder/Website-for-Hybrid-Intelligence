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
from core.database import get_word_index, page_label, retrieve
from settings import (
    ANSWER_RULES, MAX_HISTORY_CHARS, MAX_HISTORY_MESSAGES, OFF_TOPIC_ANSWER, OFF_TOPIC_DISTANCE, WORD_MATCH_FOR_TOPIC,
)


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


def citation_names(chunks):
    """The title each paper is cited with: a short version of long titles.

    "When combinations of humans and AI are useful: A systematic review and meta-analysis"
    becomes "When combinations of humans and AI are useful" (the part before the colon).
    Shorter titles make the answers shorter and quicker to write; fix_citations puts the
    full title back afterwards. Returns a dictionary: full title -> name to cite.
    """
    names = {}
    for chunk in chunks:
        title = chunk["title"]
        names[title] = title.split(":")[0].strip() if ":" in title and len(title) > 60 else title
    # Two papers with the same short title? Then those two keep their full titles.
    for title, name in names.items():
        if list(names.values()).count(name) > 1:
            names[title] = title
    return names


def build_message(question, chunks, previous_question=None):
    """Put the excerpts and the question together into the message for the AI model.

    previous_question (for a follow-up): the visitor's question before this one. A follow-up like
    "Can you elaborate more on that?" means nothing on its own, so the message says what it is about.
    """
    names = citation_names(chunks)
    parts = ["Research excerpts:\n"]
    for chunk in chunks:
        parts.append(
            "---\n"
            f"Title: {names[chunk['title']]}\n"
            f"Page: {page_label(chunk)}\n"
            f"{chunk['text']}\n"
        )
    # A real example citation, made from the first excerpt.
    example = f"[{names[chunks[0]['title']]}, p. {page_label(chunks[0])}]"
    parts.append(ANSWER_RULES.format(example=example) + "\n\n" + f"Question: {question}")
    if previous_question:
        parts.append(f'(This follows the earlier question: "{previous_question}". '
                     "Add new information about it that wasn't in your previous answer.)")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# After asking: citations and sources
# ---------------------------------------------------------------------------

def fix_citations(answer, chunks):
    """Repair citations that small models sometimes write wrongly, and put the full titles back.

      "[Excerpt 2, p. 4]"                         -> "[Hybrid Intelligence, p. 4]"
      "[Paper title: Hybrid Intelligence, p. 4]"   -> "[Hybrid Intelligence, p. 4]"
      "[The Hybrid Intelligence Manifesto, p. 6]"  -> "[The Hybrid Intelligence Manifesto: A Multi-Level ..., p. 6]"
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

    # Put the full titles back. The model cites the short titles from citation_names, or sometimes
    # shortens a title itself; both are recognised (small or capital letters don't matter).
    full_titles = {chunk["title"] for chunk in chunks}
    by_short_name = {name.lower(): title for title, name in citation_names(chunks).items()}

    def full_title(cited):
        if cited.lower() in by_short_name:
            return by_short_name[cited.lower()]
        # A title the model shortened itself: the one full title that starts with it.
        starting_with = [t for t in full_titles if len(cited) >= 10 and t.lower().startswith(cited.lower())]
        return starting_with[0] if len(starting_with) == 1 else cited

    # For each "[ ... ]": every part like "Some title, p. 3" (parts are separated by ";")
    # gets its full title. Anything else in the brackets stays as it is.
    def repair(match):
        parts = []
        for part in match.group(1).split(";"):
            cited = re.match(r"\s*(.+?)(,\s*pp?\..*)$", part)
            parts.append(full_title(cited.group(1).strip()) + cited.group(2) if cited else part.strip())
        return "[" + "; ".join(parts) + "]"

    return re.sub(r"\[([^\[\]]+)\]", repair, answer)


def cited_in(answer):
    """Which (paper title, page) pairs an answer cites, e.g. {("hybrid intelligence", "4-5")}.

    Used for follow-up questions: the excerpts the previous answer already used are avoided,
    so the AI gets new material to add, instead of repeating itself.
    """
    cited = set()
    for bracket in re.findall(r"\[([^\[\]]+)\]", answer):
        for part in bracket.split(";"):
            found = re.match(r"\s*(.+?),\s*pp?\.\s*(.+)$", part)
            if found:
                for page in found.group(2).split(","):
                    # "4–5" (long dash) and "4-5" are the same pages
                    cited.add((found.group(1).strip().lower(), page.strip().replace("–", "-")))
    return cited


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
    # In a follow-up, avoid the excerpts the previous answer already used (see cited_in).
    earlier_answers = [message["content"] for message in history if message["role"] == "assistant"]
    already_used = cited_in(earlier_answers[-1]) if earlier_answers else set()
    searched_for = search_text(question, history)
    chunks = retrieve(searched_for, avoid=already_used)

    # Nothing to do with the papers? Even the closest excerpt is far away in meaning
    # (OFF_TOPIC_DISTANCE) AND no excerpt contains most of the question's important words
    # (WORD_MATCH_FOR_TOPIC; this keeps special terms like "stochastic parrot" in).
    # Then give the fixed short answer straight away, without asking the AI.
    closest = min(chunk["distance"] for chunk in chunks)
    if closest > OFF_TOPIC_DISTANCE and get_word_index().word_match(searched_for) < WORD_MATCH_FOR_TOPIC:
        yield "text", OFF_TOPIC_ANSWER
        yield "done", {"answer": OFF_TOPIC_ANSWER, "sources": [], "chunks": chunks}
        return

    # Like stream_answer, this is a generator: each "yield" hands a piece on straight away
    # (to api.py, which sends it to the chat panel), while the pieces are also kept to
    # put the whole answer together at the end.
    earlier_questions = [message["content"] for message in history if message["role"] == "user"]
    previous_question = earlier_questions[-1] if earlier_questions else None

    pieces = []
    for piece in stream_answer(build_message(question, chunks, previous_question), history):
        pieces.append(piece)
        yield "text", piece

    answer = "".join(pieces)
    # Some models write out their thinking between <think> tags first. Remove it.
    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()
    answer = fix_citations(answer, chunks)
    # Lines with nothing but citations on them (a list of citations at the end) are removed:
    # the Sources list under the answer already shows them.
    answer = re.sub(r"^[ \t]*(\[[^\[\]]+\][ \t.]*)+$\n?", "", answer, flags=re.MULTILINE).strip()
    yield "done", {"answer": answer, "sources": find_sources(answer, chunks), "chunks": chunks}


def answer_question(question, history=None):
    """Answer one question and give back the whole answer at once (used by ask.py and /chat).

    Returns the same dictionary as the "done" step of answer_question_stream.
    """
    # Run through all the pieces without showing them, and keep only the final "done" step.
    for kind, data in answer_question_stream(question, history):
        if kind == "done":
            return data
