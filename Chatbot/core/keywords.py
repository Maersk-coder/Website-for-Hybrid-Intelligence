"""
core/keywords.py - the word search: find excerpts that contain the question's exact words.

The meaning search (core/embeddings.py) is good at everyday language, but weak at rare special
terms ("stochastic parrot", "jagged frontier", "AMIE"). The word search fills that gap.
core/database.py combines both rankings.

How the words are scored (a simplified version of a well-known method called BM25):
  - a RARE word counts a lot (e.g. "parrot": in only a few excerpts),
    a COMMON word counts very little (e.g. "human": in hundreds of excerpts)
  - a word that appears several times in an excerpt counts a bit more, but not endlessly
  - long excerpts get no advantage just for having more words

Look here when: a question with a special term doesn't find the excerpts about it.
"""

import math
import re
from collections import Counter

# Words so common they say nothing about the topic. They are left out of the word search.
STOP_WORDS = set("""
a about above after again against all also am an and any are as at be because been before being
below between both but by can could did do does doing down during each few for from further had has
have having he her here hers him his how i if in into is it its itself just me more most my no nor
not now of off on once only or other our ours out over own same she should so some such than that
the their them then there these they this those through to too under until up very was we were what
when where which while who whom why will with would you your yours tell explain describe give mean
means meaning please paper papers research study studies thing things way ways
""".split())


def words_of(text):
    """The meaningful words of a text, simplified so different forms match.

    "Parrots" and "parrot" become the same word; "the", "is" etc. are left out.
    """
    words = []
    for word in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower()):
        if len(word) < 3 or word in STOP_WORDS:
            continue
        # A simple way to treat plural and singular as the same word.
        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("s") and not word.endswith("ss") and len(word) > 4:
            word = word[:-1]
        words.append(word)
    return words


class WordIndex:
    """All the excerpts' words, counted once, so each search is quick."""

    def __init__(self, collection):
        everything = collection.get(include=["documents"])
        self.ids = everything["ids"]
        self.word_counts = [Counter(words_of(text)) for text in everything["documents"]]
        self.lengths = [sum(counts.values()) for counts in self.word_counts]
        self.average_length = sum(self.lengths) / max(len(self.lengths), 1)
        # In how many excerpts each word appears (counted once per excerpt).
        self.excerpts_with = Counter(word for counts in self.word_counts for word in counts)

    def rarity(self, word):
        """How rare (and so how telling) a word is: high for rare words, close to 0 for common ones."""
        total = len(self.ids)
        found = self.excerpts_with.get(word, 0)
        return math.log(1 + (total - found + 0.5) / (found + 0.5))

    def search(self, question, number):
        """The ids of the excerpts that best match the question's words, best first."""
        question_words = set(words_of(question))
        scores = []
        for chunk_id, counts, length in zip(self.ids, self.word_counts, self.lengths):
            score = 0.0
            for word in question_words:
                times = counts.get(word, 0)
                if times:
                    # Extra appearances count less and less; long excerpts are evened out.
                    score += self.rarity(word) * times * 2.2 / (times + 1.2 * (0.25 + 0.75 * length / self.average_length))
            if score > 0:
                scores.append((score, chunk_id))
        scores.sort(reverse=True)
        return [chunk_id for score, chunk_id in scores[:number]]

    def word_match(self, question):
        """How much of the question's important words the best excerpt contains: 0 (none) to 1 (all).

        Each word weighs as much as it is rare; a word that is in no excerpt at all weighs the most.
        Used by the off-topic check:
          "What is a stochastic parrot?"  -> "stochastic" and "parrot" are both in the same
                                              excerpts -> 1.0 -> about the papers
          "What will the weather be tomorrow?" -> "tomorrow" is in an excerpt, but "weather"
                                              (the important word) is in none -> low
        """
        question_words = set(words_of(question))
        total_weight = sum(self.rarity(word) for word in question_words)
        if not total_weight:
            return 0.0
        best = 0.0
        for counts in self.word_counts:
            found_weight = sum(self.rarity(word) for word in question_words if word in counts)
            best = max(best, found_weight / total_weight)
        return best
