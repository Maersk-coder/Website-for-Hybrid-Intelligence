"""
core/errors.py - the chatbot's own kind of error.

When something goes wrong that we expect could happen (Ollama isn't running,
the index is empty, ...), the code raises a ChatbotError with a message
written for people. ask.py prints it, api.py sends it to the chat panel.
"""


class ChatbotError(Exception):
    """A problem with a friendly message we can show to the user."""
