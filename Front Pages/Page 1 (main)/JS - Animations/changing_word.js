// CHANGING WORD: the word under the title.
// The old letters blur away, the new letters blur in one by one,
// and then a soft highlight wipes in behind the word.
class ChangingWord {
  constructor(element) {
    this.element = element;
  }

  // Animate to a new word
  show(text) {
    const el = this.element;
    const oldLetters = [...el.querySelectorAll(".cycle-letter")];
    el.classList.remove("lit");
    oldLetters.forEach((letter) => letter.classList.add("out"));

    // setTimeout runs the code inside after a delay (in milliseconds),
    // which gives the old letters time to blur away before the new ones are added
    const waitForOld = oldLetters.length ? 450 : 0;
    setTimeout(() => {
      el.textContent = "";
      [...text].forEach((character, i) => {
        const letter = document.createElement("span");
        letter.className = "cycle-letter";
        letter.style.setProperty("--i", i); // its place in the word, used for the delay
        letter.textContent = character === " " ? " " : character; // keep spaces visible
        el.appendChild(letter);
      });
      setTimeout(() => el.classList.add("lit"), 500 + text.length * 30);
    }, waitForOld);
  }

  // Show a word straight away, without animation
  showStill(text) {
    this.element.textContent = text;
    this.element.classList.add("lit");
  }
}
