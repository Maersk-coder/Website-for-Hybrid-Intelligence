// PAGE 2 · BUILD-UP: when Page 2 scrolls into view, the steps grow up from the ground one by one.
// Plays once. The animation itself is in levels_section.css; this file only decides WHEN it starts.

(() => {
  const levels = document.querySelector(".levels");  // the column holding the heading, staircase, panel and footnote

  // Some people turn off animations in their computer's settings ("reduce motion"). Respect that: skip the build-up.
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  levels.classList.add("is-waiting");  // steps flattened, text hidden, until Page 2 is in view

  // An IntersectionObserver is a "watcher" that tells us when an element comes into view on the screen
  const watcher = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {          // Page 2 is now (at least half) on screen
      levels.classList.remove("is-waiting");
      levels.classList.add("is-building");    // starts the CSS animations
      watcher.disconnect();                   // stop watching: the build-up only plays once
    }
  }, { threshold: 0.5 });                     // 0.5 = "when half of it is visible"

  watcher.observe(levels);                    // start watching
})();
