# Test questions

The questions `python tests/run_tests.py` asks the chatbot, to check the quality of its answers.
Run it again after changing something (the prompt, the chunk sizes, the model, new papers), and
compare the reports in `tests/results/` to see whether the answers got better or worse.

## How to write a question

Each question starts with `## Q` + a number + the question. Under it, these lines
(the script reads the ones in **bold**, the rest is for you):

- **Kind:** what kind of question it is (just a label, for the report).
- **Expected papers:** the file names of the papers a good answer should cite, separated by
  commas. Leave empty if no paper should be cited.
- **Not covered:** `yes` if the papers don't answer this question, so the chatbot should say so
  instead of guessing. Otherwise `no`.
- **Follow-up to:** the number of an earlier question, if this one is a follow-up to it
  (e.g. "Why is that?"). The earlier question and its answer are then sent along as the conversation.
- **A good answer:** the points a good answer contains, with the pages where they are in the
  papers. This is for you, when you score the answers. The script doesn't check it.

An empty question (`## Q11 (empty)`) is skipped. Fill in the empty ones when you add papers.

---

## Q1 What is Hybrid Intelligence?

- **Kind:** definition
- **Expected papers:** Hybrid Intelligence.pdf
- **Not covered:** no
- **A good answer:**
  - The ability to achieve complex goals by combining human and artificial intelligence, reaching
    better results than either could alone, and continuously improving by learning from each other (Hybrid Intelligence, p. 5).
  - Its three parts: tasks done *collectively*, *superior results*, *continuous learning* (p. 5).
  - Uses the complementary strengths of humans and AI (p. 2, 4).

## Q2 What are humans better at than AI, and what is AI better at?

- **Kind:** complementary strengths
- **Expected papers:** Hybrid Intelligence.pdf
- **Not covered:** no
- **A good answer:**
  - Humans: flexibility, creativity, empathy, common sense, intuition ("system 1" thinking),
    handling unusual cases (Hybrid Intelligence, p. 4-5).
  - AI: speed, consistency, recognising patterns in huge amounts of data, following
    probability rules ("system 2"-like analysis) (p. 4-5).
  - Possibly Moravec's paradox: easy for computers to pass intelligence tests, hard to match a
    one-year-old's perception and mobility (p. 4).

## Q3 Do humans and AI perform better together than alone?

- **Kind:** disagreement / benefits and risks
- **Expected papers:** When combinations of humans and.pdf
- **Not covered:** no
- **A good answer:**
  - On average, no: human–AI combinations did worse than the best of the human or the AI alone
    (Hedges' g = −0.23) (When combinations of humans and AI are useful, p. 1, 3).
  - But they did better than the human alone ("human augmentation", g = 0.64) (p. 3).
  - It depends: losses in decision tasks, gains in creation tasks; gains when the human is better
    than the AI alone, losses when the AI is better (p. 3).
  - Balanced: the Hybrid Intelligence paper describes HI as *reaching* superior results (p. 5),
    the meta-analysis finds that this usually isn't achieved yet. A great answer notes this tension.

## Q4 How many studies did the meta-analysis on human–AI combinations include, and from which years?

- **Kind:** specific facts
- **Expected papers:** When combinations of humans and.pdf
- **Not covered:** no
- **A good answer:**
  - 106 experiments with 370 effect sizes, from 74 papers (When combinations of humans and AI are useful, p. 1-2).
  - Published between January 2020 and June 2023 (p. 1-2).
  - Possibly: the search found 5,126 papers at first (p. 2).

## Q5 When does combining humans and AI work best?

- **Kind:** conditions
- **Expected papers:** When combinations of humans and.pdf
- **Not covered:** no
- **A good answer:**
  - In creation tasks (making content, like text or images) rather than decision tasks
    (When combinations of humans and AI are useful, p. 3-4).
  - When the human alone is better than the AI alone (synergy g = 0.46) (p. 3).
  - Possibly the bird-image example: AI 73%, human 81%, together 90% (p. 5).
  - Possibly: when tasks are split so each partner does what it is best at (p. 5-6).

## Q6 Why is that?

- **Kind:** follow-up
- **Expected papers:** When combinations of humans and.pdf
- **Not covered:** no
- **Follow-up to:** 5
- **A good answer:**
  - Must be about Q5's answer (tests the conversation memory).
  - When humans are better than the AI, they are also better at judging when to trust the AI and
    when to trust themselves (When combinations of humans and AI are useful, p. 5).
  - Creation tasks mix creative parts (humans) with routine filling-in (AI) (p. 4-5).

## Q7 What are the risks of letting AI take over more and more work?

- **Kind:** risks (balanced answer expected)
- **Expected papers:** Hybrid Intelligence Manifesto.pdf
- **Not covered:** no
- **A good answer:**
  - Growing reliance on AI outputs, less human engagement, loss of skills ("deskilling")
    (Hybrid Intelligence Manifesto, p. 21).
  - Value and power concentrating with whoever controls compute and capital; human judgment
    becoming economically peripheral (p. 20-21).
  - Possibly overreliance / underreliance on AI (When combinations ..., p. 3), and the need to
    balance trust and distrust (Hybrid Intelligence, p. 6).
  - Balanced: also the benefits, e.g. productivity gains and efficiency (Manifesto, p. 21).

## Q8 What are the four Hybrid Intelligence missions in the manifesto?

- **Kind:** specific facts
- **Expected papers:** Hybrid Intelligence Manifesto.pdf
- **Not covered:** no
- **A good answer:** (Hybrid Intelligence Manifesto, p. 6)
  - Interface mission: interaction designs that build human knowledge and show uncertainty.
  - Organizational mission: make HI a measurable capability and culture.
  - Macro-societal mission: markets and governance that reward human contribution.
  - Educational mission: education that prepares people to design and govern human–AI workflows.

## Q9 Why will AI soon replace all human jobs?

- **Kind:** tricky (a wrong assumption in the question)
- **Expected papers:** Hybrid Intelligence Manifesto.pdf, Hybrid Intelligence.pdf
- **Not covered:** no
- **A good answer:**
  - Does NOT go along with the assumption: the papers don't say this.
  - General AI is still a long way off; the likely future is humans and AI working together
    (Hybrid Intelligence, p. 2).
  - Whether AI-first or hybrid futures happen is decided by design and policy choices, not by
    the technology (Hybrid Intelligence Manifesto, p. 22).

## Q10 What is the best pizza in Rome?

- **Kind:** not covered
- **Expected papers:**
- **Not covered:** yes
- **A good answer:**
  - Says clearly that the papers don't cover this, and doesn't make anything up.

## Q11 (empty)

- **Kind:**
- **Expected papers:**
- **Not covered:** no
- **A good answer:**

## Q12 (empty)

- **Kind:**
- **Expected papers:**
- **Not covered:** no
- **A good answer:**

## Q13 (empty)

- **Kind:**
- **Expected papers:**
- **Not covered:** no
- **A good answer:**

## Q14 (empty)

- **Kind:**
- **Expected papers:**
- **Not covered:** no
- **A good answer:**

## Q15 (empty)

- **Kind:**
- **Expected papers:**
- **Not covered:** no
- **A good answer:**
