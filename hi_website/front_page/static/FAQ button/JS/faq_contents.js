// THEMES GUIDE: while you scroll through the FAQ, the theme you are reading is marked in the
// guide on the left (it gets the class "is-current"; the look is in faq.css).

(() => {
  const links = [...document.querySelectorAll(".faq-contents a")];
  const themes = links.map((link) => document.querySelector(link.getAttribute("href")));

  function mark() {
    // The current theme = the last one whose top has passed the line just under the menu bar
    const line = 140;
    let current = 0;
    themes.forEach((theme, i) => {
      if (theme && theme.getBoundingClientRect().top <= line) current = i;
    });
    links.forEach((link, i) => link.classList.toggle("is-current", i === current));
  }

  window.addEventListener("scroll", mark, { passive: true });
  mark();
})();
