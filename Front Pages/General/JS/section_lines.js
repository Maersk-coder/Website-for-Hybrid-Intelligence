// SECTION LINES: Page 1's slowly rippling contour lines, as a quiet background for other pages.
// It reuses BackgroundLines from Page 1 (Page 1 (main)/JS - Animations/background_lines.js),
// so the lines look exactly the same, only fainter (see General/CSS/section_lines.css).
//
// To use it, put a canvas at the start of a section:
//   <canvas class="section-lines" data-around=".levels-zone" data-ring-size="0.8" aria-hidden="true"></canvas>
//     data-around     the part of the section the loops go around (their middle is its middle)
//     data-ring-size  how big the loops are: 1 = the smallest loop is as wide as that part, 0.5 = half as wide

// Wait until the whole page has loaded, so Page 1's BackgroundLines exists (its script comes later in the page).
document.addEventListener("DOMContentLoaded", () => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.querySelectorAll(".section-lines").forEach((canvas) => {
    const section = canvas.closest("section");
    const around = section.querySelector(canvas.dataset.around);
    const ringSize = parseFloat(canvas.dataset.ringSize || "1");
    const lines = new BackgroundLines(canvas);

    // Where the loops go. BackgroundLines reads these numbers from a "layout".
    const layout = {};

    function fit() {
      const area = section.getBoundingClientRect();
      const part = around.getBoundingClientRect();
      layout.width = section.clientWidth;
      layout.height = section.clientHeight;
      layout.pixelRatio = Math.min(window.devicePixelRatio || 1, 2);   // sharp on high-resolution screens
      layout.centerX = part.left - area.left + part.width / 2;
      layout.centerY = part.top - area.top + part.height / 2;
      // The smallest loop is radius × 1.3 tall, and 1.35 times wider than tall (see drawContours).
      layout.radius = (part.width / 2 / (1.3 * 1.35)) * ringSize;
      lines.fitTo(layout);
    }

    // Draw one picture of the loops at this moment in time
    function draw(time) {
      lines.ctx.clearRect(0, 0, layout.width, layout.height);
      lines.drawContours(time, layout);
    }

    // Run about 60 times a second, but only while the section is on screen (saves battery, keeps the page quick)
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
  });
});
