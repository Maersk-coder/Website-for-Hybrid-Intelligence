// LAYOUT: works out how big the section is, and where the cloud sits on screen (in pixels).
// Every other part reads its positions from here, so they always line up.
class Layout {
  // The constructor runs once, when animation.js does "new Layout(section)".
  // "this" is the object being made; this.width, this.centerX etc. are the values it keeps.
  constructor(section) {
    this.section = section;
    this.update();
  }

  update() {
    this.width = this.section.clientWidth;
    this.height = this.section.clientHeight;
    this.wide = this.width >= 900; // false on phones and small tablets

    if (this.wide) {
      this.centerX = this.width * 0.7;   // cloud on the right, text on the left
      this.centerY = this.height * 0.46;
      this.radius = Math.min(this.height * 0.23, this.width * 0.16);
    } else {
      this.centerX = this.width * 0.5;   // cloud in the middle, behind the content
      this.centerY = this.height * 0.62;
      this.radius = Math.min(this.width * 0.32, this.height * 0.2);
    }

    this.pixelRatio = Math.min(window.devicePixelRatio || 1, 2); // sharp on high-resolution screens
  }
}
