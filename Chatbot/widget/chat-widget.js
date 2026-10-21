// CHAT WIDGET: the chat panel that talks to the chatbot server (api.py).
//
// How to put it on a website: an empty box where the panel should go, and ONE script tag:
//
//   <div id="hi-chat"></div>
//   <script src="chat-widget.js" data-api="http://127.0.0.1:8000" data-target="#hi-chat"></script>
//
//   data-api     the address of the chatbot server (change it when the server moves online)
//   data-target  where the panel goes (a CSS selector, like "#hi-chat")
//
// The panel fills the box, so the box decides its size (see Page 3/CSS/page_3_section.css).
// The script loads its own look (chat-widget.css, in the same folder), then builds the panel.

(function () {
  // ---------------------------------------------------------------------------
  // Settings and texts (change these if you want)
  // ---------------------------------------------------------------------------

  const TEXTS = {
    eyebrow: "Ask the research",
    title: 'Questions about <span class="hi-chat-highlight">Hybrid Intelligence</span> or AI?',
    intro: "Ask anything. Answers come straight from research papers, with sources you can check.",
    tryAsking: "Try asking",
    placeholderFirst: "Ask your own question…",
    placeholderFollowUp: "Ask a follow-up question…",
    working: "Reading the papers…",
    note: "Answers are written by AI from research papers and can contain mistakes.",
    newChat: "New chat",
    sources: "Sources",
    cannotReach: "The chatbot can't be reached right now. Please try again later.",
    cutOff: "The answer was cut off. Please try again.",
  };

  // The example questions on the start screen. Clicking one asks it straight away.
  const EXAMPLE_QUESTIONS = [
    "What is Hybrid Intelligence?",
    "Do humans and AI perform better together?",
    "How can humans and AI learn from each other?",
  ];

  // How many earlier messages are sent along, so follow-up questions work.
  const HISTORY_TO_SEND = 6;

  // The longest question allowed (the server refuses longer ones too).
  const MAX_QUESTION_LENGTH = 1000;

  // ---------------------------------------------------------------------------
  // Read the settings from the <script> tag
  // ---------------------------------------------------------------------------

  // "currentScript" is this <script> tag. It is only known while the file first runs, so save it now.
  const scriptTag = document.currentScript;
  const apiUrl = (scriptTag.dataset.api || "http://127.0.0.1:8000").replace(/\/+$/, "");  // no "/" at the end
  const target = document.querySelector(scriptTag.dataset.target || "#hi-chat");

  if (!target) {
    console.warn("Chat widget: no box found for", scriptTag.dataset.target || "#hi-chat");
    return;
  }

  // Load chat-widget.css from the same folder as this script. Build the panel once it has
  // loaded, so the panel never shows up unstyled for a moment.
  const style = document.createElement("link");
  style.rel = "stylesheet";
  style.href = new URL("chat-widget.css", scriptTag.src).href;
  style.onload = build;
  style.onerror = build;  // build anyway, even if the look couldn't load
  document.head.appendChild(style);

  // ---------------------------------------------------------------------------
  // Small helpers
  // ---------------------------------------------------------------------------

  // Turn text into safe HTML: characters like < and & can't act as HTML code anymore.
  // Everything that comes from the chatbot or the visitor goes through this first.
  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // The little round "HI" badge, the chatbot's logo.
  function badge(extraClass) {
    return `<span class="hi-chat-badge ${extraClass || ""}" aria-hidden="true">HI</span>`;
  }

  const ARROW_ICON =
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"></path><path d="M13 6l6 6-6 6"></path></svg>';

  const PLUS_ICON =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14"></path><path d="M5 12h14"></path></svg>';

  // Find the citations in an answer, like "[Paper title, p. 3]" or "[Title A, p. 2; Title B, pp. 4-5]".
  // Returns a list of { title, pages } in the order they appear.
  function findCitations(text) {
    const found = [];
    for (const bracket of text.matchAll(/\[([^\[\]]+)\]/g)) {
      for (const part of bracket[1].split(";")) {
        const match = part.trim().match(/^(.+?),\s*pp?\.\s*(.+)$/);
        if (match) found.push({ title: match[1].trim(), pages: match[2].trim() });
      }
    }
    return found;
  }

  // Put the sources in the order the answer first cites them, so the first one cited is number 1.
  function orderSources(answer, sources) {
    const order = [];
    for (const citation of findCitations(answer)) {
      const source = sources.find((s) => s.title === citation.title);
      if (source && !order.includes(source)) order.push(source);
    }
    return order.concat(sources.filter((s) => !order.includes(s)));
  }

  // Turn the chatbot's answer text into HTML for the panel:
  //   - citations [Long paper title, p. 3] become small numbered tags "1 · p. 3"
  //     (sources = the papers, numbered in this order: the first one is 1)
  //   - **bold** becomes bold, "- item" lines become a list, blank lines start a new paragraph
  function formatAnswer(text, sources) {
    const numbers = {};  // escaped paper title -> its number in the Sources list
    sources.forEach((source, index) => { numbers[escapeHtml(source.title)] = index + 1; });

    let html = escapeHtml(text);

    // Citations -> numbered tags. A bracket is only changed if every part of it is a known paper.
    html = html.replace(/\[([^\[\]]+)\]/g, (whole, inside) => {
      const tags = inside.split(";").map((part) => {
        const match = part.trim().match(/^(.+?),\s*pp?\.\s*(.+)$/);
        const number = match && numbers[match[1].trim()];
        return number ? `<span class="hi-chat-cite">${number} · p. ${match[2].trim()}</span>` : null;
      });
      return tags.includes(null) ? whole : tags.join(" ");
    });

    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");  // **bold**
    html = html.replace(/^#{1,6}\s*(.+)$/gm, "<strong>$1</strong>");  // "## Heading" -> bold line

    // Go through the lines: list items, normal lines, and blank lines between paragraphs.
    const parts = [];
    let paragraph = [];
    let list = [];
    const finishParagraph = () => { if (paragraph.length) parts.push(`<p>${paragraph.join("<br>")}</p>`); paragraph = []; };
    const finishList = () => { if (list.length) parts.push(`<ul>${list.join("")}</ul>`); list = []; };

    for (const line of html.split("\n")) {
      const item = line.match(/^\s*(?:[-*•]|\d+[.)])\s+(.*)$/);
      if (item) {
        finishParagraph();
        list.push(`<li>${item[1]}</li>`);
      } else if (!line.trim()) {
        finishParagraph();
        finishList();
      } else {
        finishList();
        paragraph.push(line);
      }
    }
    finishParagraph();
    finishList();
    return parts.join("");
  }

  // The "Sources" box under an answer.
  function sourcesHtml(sources) {
    if (!sources.length) return "";
    const items = sources.map((source, index) =>
      `<li><span class="hi-chat-source-number">${index + 1}</span>` +
      `<span>${escapeHtml(source.title)} <span class="hi-chat-source-pages">· p. ${escapeHtml(source.pages.join(", "))}</span></span></li>`
    );
    return `<div class="hi-chat-sources"><div class="hi-chat-sources-label">${TEXTS.sources}</div><ol>${items.join("")}</ol></div>`;
  }

  // ---------------------------------------------------------------------------
  // Build the panel and make it work
  // ---------------------------------------------------------------------------

  function build() {
    const inputId = "hi-chat-input-" + Math.random().toString(36).slice(2, 8);
    const examples = EXAMPLE_QUESTIONS.map((question) =>
      `<button type="button" class="hi-chat-example">${escapeHtml(question)}${ARROW_ICON}</button>`
    ).join("");

    // The panel's parts. Only one of "start" and "top + messages" is visible at a time.
    target.innerHTML = `
      <section class="hi-chat" aria-label="Chat with the research">
        <div class="hi-chat-top">
          <div class="hi-chat-top-title">${badge()}<h2>${TEXTS.title}</h2></div>
          <button type="button" class="hi-chat-new">${PLUS_ICON}${TEXTS.newChat}</button>
        </div>

        <div class="hi-chat-start">
          <div class="hi-chat-eyebrow">${badge()}<span>${TEXTS.eyebrow}</span></div>
          <h2 class="hi-chat-title">${TEXTS.title}</h2>
          <p class="hi-chat-intro">${TEXTS.intro}</p>
          <div class="hi-chat-try">${TEXTS.tryAsking}</div>
          <div class="hi-chat-examples">${examples}</div>
        </div>

        <div class="hi-chat-messages" role="log" aria-live="polite"></div>

        <form class="hi-chat-form">
          <div class="hi-chat-inputbox">
            <label class="hi-chat-hidden-label" for="${inputId}">Your question</label>
            <input id="${inputId}" class="hi-chat-input" type="text" autocomplete="off"
                   maxlength="${MAX_QUESTION_LENGTH}" placeholder="${TEXTS.placeholderFirst}">
            <button type="submit" class="hi-chat-send" aria-label="Send">${ARROW_ICON}</button>
          </div>
          <p class="hi-chat-note">${TEXTS.note}</p>
        </form>
      </section>`;

    const panel = target.querySelector(".hi-chat");
    const messages = panel.querySelector(".hi-chat-messages");
    const form = panel.querySelector(".hi-chat-form");
    const input = panel.querySelector(".hi-chat-input");
    const sendButton = panel.querySelector(".hi-chat-send");

    let history = [];       // the conversation so far: [{ role: "user" | "assistant", content: "..." }]
    let busy = false;       // true while an answer is on its way
    let stopRequest = null; // stops the answer that is on its way (used by "New chat")

    // Busy: the send and example buttons can't be used until the answer is finished.
    function setBusy(isBusy) {
      busy = isBusy;
      sendButton.disabled = isBusy;
      panel.querySelectorAll(".hi-chat-example").forEach((button) => { button.disabled = isBusy; });
      messages.setAttribute("aria-busy", isBusy ? "true" : "false");  // screen readers wait for the full answer
    }

    // Scroll to the newest message, but only if the visitor is already near the bottom
    // (so it doesn't pull them away while they scroll up to read something).
    function scrollDown(always) {
      const nearBottom = messages.scrollHeight - messages.scrollTop - messages.clientHeight < 120;
      if (always || nearBottom) messages.scrollTop = messages.scrollHeight;
    }

    // Add one message to the list and give back its element.
    function addMessage(kind) {
      const row = document.createElement("div");
      row.className = "hi-chat-msg is-" + kind;
      if (kind === "bot") row.innerHTML = badge("is-small") + '<div class="hi-chat-answer"></div>';
      messages.appendChild(row);
      return row;
    }

    function showError(answerBox, text) {
      answerBox.classList.add("is-error");
      answerBox.textContent = text;
    }

    // Ask one question: show it, send it to the server, and show the answer as it arrives.
    async function ask(question) {
      question = question.trim();
      if (!question || busy) return;

      panel.classList.add("is-chatting");  // switch from the start screen to the conversation
      input.value = "";
      input.placeholder = TEXTS.placeholderFollowUp;

      addMessage("user").textContent = question;
      const answerBox = addMessage("bot").querySelector(".hi-chat-answer");
      answerBox.innerHTML =
        `<span class="hi-chat-working"><span class="hi-chat-dots" aria-hidden="true"><i></i><i></i><i></i></span>${TEXTS.working}</span>`;
      scrollDown(true);
      setBusy(true);

      const controller = new AbortController();
      stopRequest = () => controller.abort();

      try {
        const response = await fetch(apiUrl + "/chat/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: question, history: history.slice(-HISTORY_TO_SEND) }),
          signal: controller.signal,
        });

        // Refused before answering (too long, too many questions, ...): show the server's message.
        if (!response.ok) {
          const problem = await response.json().catch(() => ({}));
          showError(answerBox, problem.detail || TEXTS.cannotReach);
          return;
        }

        // The answer arrives as lines of JSON, a few words at a time (see api.py, /chat/stream).
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let waiting = "";   // text received that isn't a complete line yet
        let written = "";   // the answer so far
        let finished = false;

        while (!finished) {
          const { value, done } = await reader.read();
          if (done) break;
          waiting += decoder.decode(value, { stream: true });
          const lines = waiting.split("\n");
          waiting = lines.pop();  // the last piece may be an unfinished line: keep it for later

          for (const line of lines) {
            if (!line.trim()) continue;
            const event = JSON.parse(line);

            if (event.type === "text") {
              written += event.text;
              // While it's being written: hide a citation that isn't finished yet (no "]" yet),
              // and number the papers in the order they are cited so far (the same order as at the end).
              const shown = written.replace(/\[[^\[\]]*$/, "");
              const titles = [...new Set(findCitations(shown).map((citation) => citation.title))];
              answerBox.innerHTML = formatAnswer(shown, titles.map((title) => ({ title })));
              scrollDown(false);
            } else if (event.type === "done") {
              // The full answer (citations repaired by the server) with the numbered sources.
              const sources = orderSources(event.answer, event.sources);
              answerBox.innerHTML = formatAnswer(event.answer, sources) + sourcesHtml(sources);
              history.push({ role: "user", content: question }, { role: "assistant", content: event.answer });
              finished = true;
              scrollDown(false);
            } else if (event.type === "error") {
              showError(answerBox, event.detail);
              finished = true;
            }
          }
        }
        if (!finished) showError(answerBox, TEXTS.cutOff);
      } catch (error) {
        if (error.name !== "AbortError") showError(answerBox, TEXTS.cannotReach);  // AbortError = "New chat" was clicked
      } finally {
        if (stopRequest) stopRequest = null;
        setBusy(false);
      }
    }

    // Start over: forget the conversation and show the start screen again.
    function newChat() {
      if (stopRequest) stopRequest();
      history = [];
      messages.innerHTML = "";
      panel.classList.remove("is-chatting");
      input.placeholder = TEXTS.placeholderFirst;
      input.focus();
    }

    form.addEventListener("submit", (event) => {
      event.preventDefault();  // stop the browser from reloading the page
      ask(input.value);
    });
    panel.querySelectorAll(".hi-chat-example").forEach((button) => {
      button.addEventListener("click", () => ask(button.textContent));
    });
    panel.querySelector(".hi-chat-new").addEventListener("click", newChat);
  }
})();
