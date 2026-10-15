// HEADER HIDE: the menu bar is shown on Pages 1, 2 and 3, and fades away on Page 4.
// It works however the page is scrolled: mouse wheel, trackpad, scrollbar or keyboard.

(() => {
  const header = document.querySelector(".site-header");   // the menu bar
  const page4 = document.querySelector(".page-4");         // Page 4, the page where the menu bar should be gone

  function update() {
    // Where is the top of Page 4 on the screen right now?
    // 0 = at the very top of the screen, window.innerHeight = at the very bottom. Further down = bigger number.
    const page4Top = page4.getBoundingClientRect().top;

    // As soon as Page 4 has come 10% up onto the screen: hide the menu bar.
    // Otherwise (Pages 1, 2 and 3): show it.
    header.classList.toggle("is-hidden", page4Top < window.innerHeight * 0.9);
  }

  window.addEventListener("scroll", update, { passive: true });  // check every time the page moves
  update();                                                       // and once right away, in case the page opens further down
})();
