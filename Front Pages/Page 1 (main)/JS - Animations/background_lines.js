// BACKGROUND LINES: everything flat that is drawn behind the cloud:
//  - the flowing contour loops around the cloud
//  - the dashed pointer lines from the labels to the cloud
class BackgroundLines {
  constructor(canvas) {
    this.canvas = canvas;
    // ctx is the "pen" for the canvas: beginPath, moveTo, lineTo and stroke draw a line
    this.ctx = canvas.getContext("2d");
  }

  // Match the drawing surface to the size of the section
  fitTo(layout) {
    const r = layout.pixelRatio;
    this.canvas.width = layout.width * r;
    this.canvas.height = layout.height * r;
    this.ctx.setTransform(r, 0, 0, r, 0, 0);
  }

  // Draw one frame. "pointers" comes from Labels.pointers()
  draw(time, layout, pointers) {
    this.ctx.clearRect(0, 0, layout.width, layout.height);
    this.drawContours(time, layout);
    this.drawPointers(pointers);
  }

  // Nested, slowly rippling loops around the cloud
  drawContours(time, layout) {
    const ctx = this.ctx;
    const { centerX, centerY, radius } = layout;
    const rings = SETTINGS.contourRings;
    ctx.lineWidth = 1;

    for (let k = 0; k < rings; k++) {
      const size = radius * (1.3 + k * 0.16); // each ring a bit bigger than the last
      const ringX = centerX - k * radius * SETTINGS.contourDrift; // and a bit further to the left
      ctx.beginPath();
      for (let s = 0; s <= 120; s++) {
        const a = (s / 120) * Math.PI * 2;
        const ripple =
          1 +
          0.06 * Math.sin(3 * a + time * 0.25 + k * 0.35) +
          0.04 * Math.sin(5 * a - time * 0.18 + k * 0.6);
        const x = ringX + Math.cos(a) * size * ripple * 1.35; // 1.35 = a bit wider than tall
        const y = centerY + Math.sin(a) * size * ripple;
        s === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = `rgba(${SETTINGS.lineColor}, ${Math.max(0.05, 0.16 - k * 0.005)})`; // outer rings are fainter
      ctx.stroke();
    }
  }

  // Dashed lines from the labels, with a small square where they touch the cloud
  drawPointers(pointers) {
    const ctx = this.ctx;
    const color = SETTINGS.lineColor;

    pointers.forEach((p) => {
      ctx.strokeStyle = `rgba(${color}, ${p.active ? 0.7 : 0.35})`;
      ctx.setLineDash([3, 4]);
      ctx.beginPath();
      ctx.moveTo(p.fromX, p.fromY);
      ctx.lineTo(p.toX, p.toY);
      ctx.stroke();

      ctx.setLineDash([]);
      ctx.strokeRect(p.toX - 3, p.toY - 3, 6, 6);
      if (p.active) {
        // a bigger focus box around the point of the label that is lit up
        ctx.strokeStyle = `rgba(${color}, 0.3)`;
        ctx.strokeRect(p.toX - 14, p.toY - 14, 28, 28);
      }
    });
  }
}
