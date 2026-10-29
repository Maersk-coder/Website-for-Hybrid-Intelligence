// SHAPE TIMELINE: the clock that decides when the cloud changes shape.
// Each shape stays for a while ("hold"), then changes into the next one ("morph").
// It doesn't draw anything itself. animation.js hands it two functions, and it calls them:
//   onChangeStart(nextPhase)          - a change is starting (good moment to swap the word)
//   onShapeReached(phase, nextPhase)  - the change is finished, the next shape is now showing
class ShapeTimeline {
  constructor({ onChangeStart, onShapeReached }) {
    this.phases = SETTINGS.phases;
    this.onChangeStart = onChangeStart;
    this.onShapeReached = onShapeReached;
    this.phase = 0;        // which shape is showing now
    this.time = 0;         // seconds since this shape appeared
    this.changing = false;
  }

  // Move the clock forward by dt seconds. Returns how far through a change we are (0 to 1).
  update(dt) {
    const hold = SETTINGS.holdSeconds;
    const morph = SETTINGS.morphSeconds;
    const count = this.phases.length;
    this.time += dt;

    if (this.time >= hold + morph) {
      // change finished: the next shape becomes the current one
      this.phase = (this.phase + 1) % count;
      this.time = 0;
      this.changing = false;
      this.onShapeReached(this.phase, (this.phase + 1) % count);
      return 0;
    }

    if (this.time > hold) {
      if (!this.changing) {
        this.changing = true;
        this.onChangeStart((this.phase + 1) % count);
      }
      return ShapeTimeline.ease((this.time - hold) / morph);
    }

    return 0;
  }

  // starts slowly, speeds up, and slows down again at the end
  static ease(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }
}
