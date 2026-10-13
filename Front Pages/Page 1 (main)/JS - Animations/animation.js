// ANIMATION: the conductor. It creates all the parts, connects them,
// and runs them every frame. The parts themselves live in their own files:
//   settings.js          all the numbers and colours
//   layout.js            where the cloud sits and how big it is
//   shapes.js            the three shapes (human, machine, hybrid)
//   dot_cloud.js         the 3D cloud of dots
//   shape_timeline.js    when the shape changes
//   changing_word.js     the word under the title
//   labels.js            the four labels and their pointer lines
//   background_lines.js  the contour loops and drawing the pointer lines

// The (() => { ... })() wrapper keeps the names below private to this file.
(() => {
  const section = document.querySelector(".animation-section");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const phases = SETTINGS.phases;

  // Create the parts. "new Layout(section)" builds an object from the Layout class in layout.js,
  // and from then on we use it through its methods, like layout.update().
  // cloud = the 3D dots, lines = the drawn lines, labels = the four boxes, word = the changing word.
  const layout = new Layout(section);
  const cloud = new DotCloud(section.querySelector(".animation-cloud"));
  const lines = new BackgroundLines(section.querySelector(".animation-canvas"));
  const labels = new Labels(section);
  const word = new ChangingWord(section.querySelector(".cycle-word"));

  // Connect them. The timeline only keeps time; we give it two functions,
  // and it calls them when a shape change starts and when it is finished.
  const timeline = new ShapeTimeline({
    onChangeStart: (next) => {
      word.show(phases[next].word);
      labels.next();
    },
    onShapeReached: (current, next) => {
      cloud.showShapes(phases[current].shape, phases[next].shape);
    },
  });

  // Mouse: tilts the cloud a little 
  const mouse = { x: 0, y: 0 };
  const tilt = { x: 0, y: 0 };
  section.addEventListener("mousemove", (e) => {
    const rect = section.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1; // -1 = left edge, 1 = right edge
    mouse.y = ((e.clientY - rect.top) / rect.height) * 2 - 1; // -1 = top, 1 = bottom
  });
  section.addEventListener("mouseleave", () => { mouse.x = 0; mouse.y = 0; });

  // Size: recalculate everything when the window changes size 
  function fit() {
    layout.update();
    cloud.fitTo(layout);
    lines.fitTo(layout);
    labels.place(layout);
  }

  // One frame, about 60 times a second. dt is the seconds since the last frame,
  // so the speed is the same on fast and slow screens.
  let time = 0;
  let spin = 0;

  function frame(dt) {
    time += dt;
    spin += dt * SETTINGS.spinSpeed;
    // the tilt moves a small step towards the mouse each frame, which makes it smooth
    tilt.x += (mouse.x - tilt.x) * SETTINGS.tiltSmoothness;
    tilt.y += (mouse.y - tilt.y) * SETTINGS.tiltSmoothness;

    cloud.setMix(timeline.update(dt));
    cloud.render(time, 0.15 + tilt.y * 0.25, spin + tilt.x * SETTINGS.tiltAmount);
    lines.draw(time, layout, labels.pointers(cloud, layout));
  }

  // Run. requestAnimationFrame asks the browser to call loop() again before it next updates the screen.
  let running = true;
  let last = 0;

  function loop(now) {
    const dt = Math.min(0.05, (now - last) / 1000 || 0.016); // seconds since the last frame
    last = now;
    if (running) frame(dt);
    requestAnimationFrame(loop);
  }

  // stop drawing while the section is scrolled out of view (saves battery, and keeps the rest of the page quick).
  // It only counts as "in view" when at least 1% of it is on screen. (When Page 2 fills the screen, Page 1's
  // bottom edge still touches the top of the screen, and the browser would otherwise count that as "in view".)
  new IntersectionObserver(([entry]) => (running = entry.intersectionRatio >= 0.01), { threshold: 0.01 }).observe(section);

  window.addEventListener("resize", () => {
    fit();
    if (reduceMotion) drawStill();
  });

  // for people who turn off motion: show the infinity shape and its word, without movement
  function drawStill() {
    const finalPhase = phases[phases.length - 1];
    cloud.showShapes(finalPhase.shape, finalPhase.shape);
    cloud.setMix(0);
    cloud.render(0, 0.15, 0.5);
    lines.draw(0, layout, labels.pointers(cloud, layout));
  }

  fit();
  if (reduceMotion) {
    word.showStill(phases[phases.length - 1].word);
    drawStill();
  } else {
    word.show(phases[0].word);
    requestAnimationFrame(loop);
  }
})();
