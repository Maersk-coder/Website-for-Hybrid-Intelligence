// SECTION JUMP: one scroll of the mouse wheel = glide to the next (or previous) section.
// Scrolling again while it glides changes course right away, so fast scrolling never waits.

const sections = document.querySelectorAll("section");  // every section on the page, top to bottom
let target = 0;          // the section we are on, or gliding to
let lastScrollTime = 0;  // when the wheel last moved
let lastDirection = 0;   // 1 = last scroll was down, -1 = up
let lastJumpTime = 0;    // when the last jump started

// Which section is on screen? The one whose top is closest to the top of the screen.
function sectionOnScreen() {
  let closest = 0;
  sections.forEach((section, i) => {
    const distance = Math.abs(section.getBoundingClientRect().top);
    if (distance < Math.abs(sections[closest].getBoundingClientRect().top)) closest = i;
  });
  return closest;
}

window.addEventListener("wheel", (event) => {
  if (event.ctrlKey) return;  // Ctrl + wheel = zoom in/out, so leave that alone
  event.preventDefault();     // stop the browser's normal, slow scrolling

  const now = Date.now();                       // the time right now, in milliseconds
  const direction = event.deltaY > 0 ? 1 : -1;  // deltaY above 0 = scrolling down, below 0 = up
  // A new scroll = the wheel was still for a moment, or it turned the other way.
  // (A trackpad keeps sending small scrolls for a second after you let go: those don't count.)
  const newScroll = now - lastScrollTime > 60 || direction !== lastDirection;
  lastScrollTime = now;
  lastDirection = direction;
  if (!newScroll) return;

  // Not gliding right now? Then start from the section on screen
  // (in case the page was moved another way, like dragging the scrollbar).
  if (now - lastJumpTime > 1000) target = sectionOnScreen();

  // One section further, but never past the first or the last one
  target = Math.min(Math.max(target + direction, 0), sections.length - 1);
  sections[target].scrollIntoView({ behavior: "smooth" });  // glide there (changes course if already gliding)
  lastJumpTime = now;
}, { passive: false });  // "passive: false" is needed, or the browser won't let us stop the normal scrolling
