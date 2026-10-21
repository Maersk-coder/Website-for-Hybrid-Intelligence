// PAGE 3 LINES: Page 1's slowly rippling contour lines, drawn behind the chat panel.
// It reuses BackgroundLines from Page 1 (Page 1 (main)/JS - Animations/background_lines.js),
// so the lines look exactly the same. The loops sit around the chat panel and peek out on both sides.

(() => {
  const section = document.querySelector(".page-3");
  const canvas = section.querySelector(".page-3-lines");
  const chat = section.querySelector(".page-3-chat");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const lines = new BackgroundLines(canvas);

  // Where the loops go: their middle is the middle of the chat panel, and the smallest loop
  // is just a little wider than the panel. (BackgroundLines reads these from a "layout".)
  const layout = {};

  function fit() {
    const area = section.getBoundingClientRect();
    const panel = chat.getBoundingClientRect();
    layout.width = section.clientWidth;
    layout.height = section.clientHeight;
    layout.pixelRatio = Math.min(window.devicePixelRatio || 1, 2);   // sharp on high-resolution screens
    layout.centerX = panel.left - area.left + panel.width / 2;
    layout.centerY = panel.top - area.top + panel.height / 2;
    // The smallest loop is radius × 1.3 tall and × 1.35 wider than that (see drawContours):
    // this makes it about 8% wider than the panel.
    layout.radius = (panel.width / 2 / (1.3 * 1.35)) * 1.08;
    lines.fitTo(layout);
  }

  // Draw one picture of the loops at this moment in time
  function draw(time) {
    lines.ctx.clearRect(0, 0, layout.width, layout.height);
    lines.drawContours(time, layout);
  }

  // Run about 60 times a second, but only while Page 3 is on screen (saves battery, keeps the page quick)
  let running = false;
  let time = 0;
  let last = 0;

  function loop(now) {
    const dt = Math.min(0.05, (now - last) / 1000 || 0.016);  // seconds since the last frame
    last = now;
    if (running) {
      time += dt;
      draw(time);
    }
    requestAnimationFrame(loop);
  }

  new IntersectionObserver(([entry]) => (running = entry.intersectionRatio >= 0.01), { threshold: 0.01 }).observe(section);

  window.addEventListener("resize", () => {
    fit();
    draw(time);
  });

  fit();
  draw(0);
  if (!reduceMotion) requestAnimationFrame(loop);  // people who turn off motion see the lines standing still
})();
