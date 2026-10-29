// LABELS: the four small boxes around the cloud (Individual, Workflow, Organization, Society & Economy).
// Places them around the cloud, lights up one at a time,
// and works out where each dashed pointer line should start and end.
class Labels {
  constructor(section) {
    this.items = [...section.querySelectorAll(".animation-label")];
    this.positions = [];  // top-left corner of each label, in pixels
    this.activeIndex = 0;
    this.setActive(0);
  }

  // Put each label in its spot around the cloud (spots are in SETTINGS.labelSpots)
  place(layout) {
    this.positions = this.items.map((label, i) => {
      const [right, down] = SETTINGS.labelSpots[i];
      const x = layout.centerX + right * layout.radius;
      const y = layout.centerY + down * layout.radius;
      label.style.transform = `translate(${x}px, ${y}px)`; // moves the label to x, y
      return { x, y };
    });
  }

  // Light up one label
  setActive(index) {
    this.activeIndex = index;
    this.items.forEach((label, i) => label.classList.toggle("active", i === index));
  }

  // Light up the next label
  next() {
    this.setActive((this.activeIndex + 1) % this.items.length);
  }

  // The pointer lines: from the side of each label to its point on the cloud
  pointers(cloud, layout) {
    if (!cloud.ready || !layout.wide) return []; // no lines on phones (labels are hidden there)
    return this.items.map((label, i) => {
      const target = cloud.toScreen(SETTINGS.labelTargets[i], layout);
      const { x, y } = this.positions[i];
      const startX = x > target.x ? x : x + label.offsetWidth; // start on the side facing the cloud
      return {
        fromX: startX,
        fromY: y + label.offsetHeight / 2,
        toX: target.x,
        toY: target.y,
        active: i === this.activeIndex,
      };
    });
  }
}
