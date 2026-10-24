"""
core/ - the machinery of the chatbot. You don't run these files yourself:
ingest.py, ask.py, api.py and check.py use them.

  errors.py     ChatbotError: a problem with a friendly message
  pdf_text.py   read a PDF, clean its text, find its title
  chunks.py     cut the text into chunks
  embeddings.py turn text into numbers for searching (Ollama: nomic-embed-text)
  keywords.py   the word search: excerpts with the question's rare words ("stochastic parrot")
  database.py   ChromaDB: store chunks and search them (meaning + words combined)
  ai_model.py   talk to the AI model (Ollama)
  answers.py    answer a question: search, ask the AI, repair citations, find sources
"""
