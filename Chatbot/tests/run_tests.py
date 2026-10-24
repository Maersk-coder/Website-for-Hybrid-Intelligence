"""
tests/run_tests.py - asks the chatbot all the questions in tests/test_questions.md and saves a report.

The report goes in tests/results/, named after the date and time (e.g. 2026-10-22_1730.md).
For each question it shows the answer, the sources, how long it took, a few automatic checks,
and an empty score for you to fill in. Run it again after changing something, and compare reports.

How to run it (inside the Chatbot folder, with the virtual environment on, and Ollama running):
  python tests/run_tests.py              all questions (takes about 10-15 minutes on a laptop)
  python tests/run_tests.py --only 3,6   only some questions (a follow-up also runs the question before it)
"""

import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# This file is in the tests/ folder, but needs settings.py and core/ from the folder above.
# This line lets Python find them there.
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ai_model import model_description          # noqa: E402  (imported after the line above on purpose)
from core.answers import answer_question_stream      # noqa: E402
from core.database import page_label                 # noqa: E402
from core.errors import ChatbotError                 # noqa: E402
from settings import CHUNK_MAX_WORDS, CHUNK_MIN_WORDS, NUMBER_OF_CHUNKS  # noqa: E402

HERE = Path(__file__).parent
QUESTIONS_FILE = HERE / "test_questions.md"
RESULTS_FOLDER = HERE / "results"

# Words that show the chatbot said "the papers don't cover this".
SAYS_NOT_COVERED = re.compile(
    r"(do not|don't|does not|doesn't|did not|didn't) (cover|contain|mention|address|discuss|include|provide)"
    r"|not covered|no information|cannot be answered|can't be answered|not (addressed|discussed|mentioned) in"
    # The off-topic answer (OFF_TOPIC_ANSWER in settings.py) and the AI's own "try elsewhere" replies.
    # (Not just "Google": a real answer can mention Google, e.g. "uses more energy than a Google search".)
    r"|not something I can help with|search(ing)? elsewhere|try (a )?search engine",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Reading the questions
# ---------------------------------------------------------------------------

def read_questions():
    """Read test_questions.md and return a list of questions (dictionaries)."""
    text = QUESTIONS_FILE.read_text(encoding="utf-8")
    questions = []
    # Each question starts with a line like "## Q3 Do humans and AI ...?". re.split cuts the text
    # at those lines, and keeps the number and the question (the two groups in the pattern).
    parts = re.split(r"^## Q(\d+)[ \t]+(.*)$", text, flags=re.MULTILINE)
    # parts = [text before Q1, "1", "What is ...?", text of Q1, "2", "What are ...?", text of Q2, ...]
    for number, question, body in zip(parts[1::3], parts[2::3], parts[3::3]):
        question = question.strip()
        if question.startswith("(empty)"):
            continue

        def field(name):
            """The value after "- **name:**" in this question's text ("" if it isn't there)."""
            found = re.search(rf"^- \*\*{name}:\*\*[ \t]*(.*)$", body, flags=re.MULTILINE)
            return found.group(1).strip() if found else ""

        good_answer = body.split("**A good answer:**", 1)[1].strip() if "**A good answer:**" in body else ""
        follow_up = field("Follow-up to")
        questions.append({
            "number": int(number),
            "question": question,
            "kind": field("Kind"),
            "expected_papers": [name.strip() for name in field("Expected papers").split(",") if name.strip()],
            "not_covered": field("Not covered").lower().startswith("y"),
            "follow_up_to": int(follow_up) if follow_up.isdigit() else None,
            "good_answer": good_answer,
        })
    return questions


# ---------------------------------------------------------------------------
# Asking one question
# ---------------------------------------------------------------------------

def ask(test, earlier):
    """Ask one test question. earlier = the results so far (for follow-up questions)."""
    history = []
    parent = earlier.get(test["follow_up_to"])
    if parent:
        history = [{"role": "user", "content": parent["question"]},
                   {"role": "assistant", "content": parent["answer"]}]

    start = time.time()
    first_words = None
    for kind, data in answer_question_stream(test["question"], history):
        if kind == "text" and first_words is None:
            first_words = time.time() - start
        elif kind == "done":
            result = data
    total = time.time() - start

    # Compare only the file names, not the folders, so moving a PDF to another subfolder of papers/
    # doesn't break the test questions. Path(...).name = "Pro AI/paper.pdf" -> "paper.pdf"
    cited = {Path(source["file_name"]).name for source in result["sources"]}
    found = {Path(chunk["file_name"]).name for chunk in result["chunks"]}
    says_not_covered = bool(SAYS_NOT_COVERED.search(result["answer"]))

    return {
        **test,
        "answer": result["answer"],
        "sources": result["sources"],
        "chunks": result["chunks"],
        "seconds": total,
        "first_words": first_words or total,
        # The automatic checks. None = doesn't apply to this question.
        "search_found": all(p in found for p in test["expected_papers"]) if test["expected_papers"] else None,
        "cites_expected": all(p in cited for p in test["expected_papers"]) if test["expected_papers"] else None,
        "not_covered_ok": says_not_covered == test["not_covered"],
        "says_not_covered": says_not_covered,
        "had_history": bool(history),
    }


# ---------------------------------------------------------------------------
# Writing the report
# ---------------------------------------------------------------------------

def mark(check):
    """✓ for a passed check, ✗ for a failed one, - when it doesn't apply."""
    return "-" if check is None else ("✓" if check else "✗")


def write_report(results, started):
    """Save the results as a Markdown file in tests/results/ and return its path."""
    RESULTS_FOLDER.mkdir(exist_ok=True)
    path = RESULTS_FOLDER / f"{started:%Y-%m-%d_%H%M}.md"

    lines = [
        f"# Test results {started:%Y-%m-%d %H:%M}",
        "",
        f"- **Model:** {model_description()}",
        f"- **Chunks per question:** {NUMBER_OF_CHUNKS}, chunk size {CHUNK_MIN_WORDS}-{CHUNK_MAX_WORDS} words",
        f"- **Questions:** {len(results)}, average time {sum(r['seconds'] for r in results) / len(results):.0f} s",
        "",
        "Automatic checks: **Search** = the search found the expected paper(s); **Cited** = the answer cites them;",
        "**Not covered** = it said \"not covered\" exactly when it should. Fill in **Score** (1-5) yourself.",
        "",
        "| # | Question | Time | Search | Cited | Not covered | Score |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['number']} | {r['question']} | {r['seconds']:.0f} s | {mark(r['search_found'])} | "
                     f"{mark(r['cites_expected'])} | {mark(r['not_covered_ok'])} |  |")

    for r in results:
        lines += ["", "---", "", f"## Q{r['number']} {r['question']}", ""]
        lines.append(f"*{r['kind']}* · {r['seconds']:.0f} s (first words after {r['first_words']:.0f} s)"
                     + (f" · follow-up to Q{r['follow_up_to']}" if r["had_history"] else ""))
        lines += ["", "### Answer", "", r["answer"], "", "### Sources cited", ""]
        if r["sources"]:
            lines += [f"- {s['title']}, p. {', '.join(s['pages'])} ({s['file_name']})" for s in r["sources"]]
        else:
            lines.append("- none")
        lines += ["", "### Excerpts the search found (lower distance = closer match)", ""]
        lines += [f"- {c['title'][:70]}, p. {page_label(c)} (distance {c['distance']:.2f})" for c in r["chunks"]]
        lines += ["", "### Checks", ""]
        if r["expected_papers"]:
            lines.append(f"- Expected papers: {', '.join(r['expected_papers'])}")
            lines.append(f"- Search found them: {mark(r['search_found'])}  ·  Answer cites them: {mark(r['cites_expected'])}")
        lines.append(f"- Should say \"not covered\": {'yes' if r['not_covered'] else 'no'}  ·  "
                     f"Said it: {'yes' if r['says_not_covered'] else 'no'}  {mark(r['not_covered_ok'])}")
        lines += ["", "### A good answer (from test_questions.md)", "", r["good_answer"],
                  "", "### Your score (1-5) and notes", "", "Score: ", "", "Notes: "]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Start here
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Ask the chatbot the test questions and save a report.")
    parser.add_argument("--only", help="only these question numbers, e.g. 3,6")
    args = parser.parse_args()

    questions = read_questions()
    if args.only:
        wanted = {int(n) for n in args.only.split(",") if n.strip().isdigit()}
        # A follow-up question needs the question before it, so that one runs too.
        wanted |= {q["follow_up_to"] for q in questions if q["number"] in wanted and q["follow_up_to"]}
        questions = [q for q in questions if q["number"] in wanted]

    started = datetime.now()
    print(f"Asking {len(questions)} questions ({model_description()}). This takes a while...\n")
    results = {}
    for test in questions:
        print(f"Q{test['number']}: {test['question']}")
        try:
            result = ask(test, results)
        except ChatbotError as error:
            print(f"\nStopped: {error}\n(Run  python check.py  to see what's wrong.)")
            sys.exit(1)
        results[test["number"]] = result
        checks = f"search {mark(result['search_found'])}  cited {mark(result['cites_expected'])}  " \
                 f"not-covered {mark(result['not_covered_ok'])}"
        print(f"     {result['seconds']:.0f} s   {checks}")

    path = write_report(list(results.values()), started)
    print(f"\nReport saved: tests/results/{path.name}  (open it in VS Code, and fill in the scores)")
