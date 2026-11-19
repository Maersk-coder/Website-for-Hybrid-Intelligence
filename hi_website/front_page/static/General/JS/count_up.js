// COUNT UP: numbers with data-count="17" count up from 0 to 17 when the page opens (the page headings).
// The real number is already written in the page, so without JavaScript (or with motion turned off)
// it is simply shown as it is.
// data-suffix="%" (optional) is written after the number while it counts, e.g. 0% ... 60%.

(() => {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  document.querySelectorAll("[data-count]").forEach((element) => {
    const target = parseInt(element.dataset.count, 10);
    const suffix = element.dataset.suffix || "";   // e.g. "%", or nothing
    const duration = 1400;                     // milliseconds
    const delay = 700;                         // start once the heading has risen in
    let start = null;

    function step(now) {
      if (start === null) start = now;
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);   // fast at first, slowing down at the end
      element.textContent = Math.round(target * eased) + suffix;
      if (progress < 1) requestAnimationFrame(step);
    }

    element.textContent = "0" + suffix;
    setTimeout(() => requestAnimationFrame(step), delay);
  });
})();
