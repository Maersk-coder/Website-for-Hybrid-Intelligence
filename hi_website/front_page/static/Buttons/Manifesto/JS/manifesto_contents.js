// CONTENTS GUIDE (ECON and Education Manifesto pages): while you scroll, the part you are reading is
// marked in the Contents list on the left (it gets the class "is-current"; the look is in manifesto.css).
// Works like the FAQ page's Themes guide (Buttons/JS/faq_contents.js).

(() => {
  const links = [...document.querySelectorAll(".page-contents a")];
  const parts = links.map((link) => document.querySelector(link.getAttribute("href")));

  function mark() {
    // The current part = the last one whose top has passed the line just under the menu bar
    const line = 140;
    let current = 0;
    parts.forEach((part, i) => {
      if (part && part.getBoundingClientRect().top <= line) current = i;
    });
    links.forEach((link, i) => link.classList.toggle("is-current", i === current));
  }

  window.addEventListener("scroll", mark, { passive: true });
  mark();
})();
