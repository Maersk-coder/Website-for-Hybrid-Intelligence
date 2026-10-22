"""
ask.py - ask the chatbot questions in the terminal (for testing; the website uses api.py).

How to run it (inside the Chatbot folder, with the virtual environment on):
  python ask.py                  ask questions, see answers and sources
  python ask.py --show-chunks    also show the excerpts that were found for each question

Type a question and press Enter. Follow-up questions work: the chatbot remembers
the last few questions and answers. Type "new" to start a fresh conversation,
"quit" (or press Ctrl+C) to stop.

--show-chunks is the best tool when an answer is poor: if the right passage isn't
among the excerpts found, the problem is the search, not the AI model.
"""

import argparse
import sys

from core.answers import answer_question
from core.database import page_label
from core.errors import ChatbotError


def show_chunks(chunks):
    """Print the excerpts that were retrieved, so you can check the search."""
    print("\n--- Excerpts found (lower distance = closer match) ---")
    for number, chunk in enumerate(chunks, start=1):
        print(f"\n[{number}] {chunk['title']}, p. {page_label(chunk)}   (distance {chunk['distance']:.2f})")
        # The first 400 characters are usually enough to see what it's about.
        print("    " + chunk["text"][:400].replace("\n", " ") + " ...")
    print("\n" + "-" * 55)


def show_sources(sources):
    """Print the list of papers the answer cites."""
    if not sources:
        print("\nSources: none cited")
        return
    print("\nSources:")
    for source in sources:
        pages = ", ".join(source["pages"])
        print(f"  - {source['title']}, p. {pages}   ({source['file_name']})")


def main():
    # Print special characters (like é or –) correctly in the terminal.
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Ask the Hybrid Intelligence chatbot questions.")
    parser.add_argument("--show-chunks", action="store_true",
                        help="also print the excerpts that were found for each question")
    args = parser.parse_args()

    print("Ask a question about AI and Hybrid Intelligence. Type 'quit' to stop, 'new' to start over.")

    # The conversation so far, so follow-up questions ("tell me more") work.
    history = []

    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):  # Ctrl+C or Ctrl+Z
            print()
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            break
        if question.lower() == "new":
            history = []
            print("Started a new conversation.")
            continue

        print("Thinking...")
        try:
            result = answer_question(question, history)
        except ChatbotError as error:
            print(f"\n{error}")
            continue

        # Remember this question and answer for the next follow-up.
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": result["answer"]})

        if args.show_chunks:
            show_chunks(result["chunks"])
        print(f"\nBot: {result['answer']}")
        show_sources(result["sources"])

    print("Bye!")


if __name__ == "__main__":
    main()
