// SECTION JUMP: one scroll of the mouse wheel = glide to the next (or previous) section.
// Scrolling again while it glides changes course right away, so fast scrolling never waits.

const sections = document.querySelectorAll("section");  // every section on the page, top to bottom
let target = 0;          // the section we are on, or gliding to
let lastScrollTime = 0;  // when the wheel last moved
let lastDirection = 0;   // 1 = last scroll was down, -1 = up
let lastJumpTime = 0;    // when the last jump started
let lastStrength = 0;    // how strong the last scroll signal was

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

  // Mostly sideways (a trackpad often sends a few of these)? Not up or down, so ignore it.
  // Without this, a sideways signal counted as "scroll up" and could turn the page around.
  if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;

  // The moment you actually scrolled, in milliseconds. (Not "now": when the page is busy, for example
  // while Page 1's dot cloud is drawing, the browser can hand over several scrolls at once, and they would
  // look closer together than they really were.)
  const now = event.timeStamp;
  const direction = event.deltaY > 0 ? 1 : -1;  // deltaY above 0 = scrolling down, below 0 = up
  const strength = Math.abs(event.deltaY);      // how strong this scroll signal is

  // Does this scroll signal start a new jump? (A trackpad keeps sending weaker and weaker signals for
  // about a second after you let go. Those are the old scroll "rolling out" and must not count.)
  const paused = now - lastScrollTime > 60;     // the wheel was still for a moment
  const turned = direction !== lastDirection;   // it turned the other way
  const pushedAgain =                           // a new swipe while the old one is still rolling out:
    strength > lastStrength * 2 &&              //   the signal suddenly gets twice as strong,
    strength > 20 &&                            //   it's a real push, not a tiny wobble,
    now - lastJumpTime > 300;                   //   and the last jump didn't JUST start (a swipe starts weak and builds up)
  const keepGoing =                             // still scrolling after the last glide has finished:
    now - lastJumpTime > 600 &&                 //   the last jump had 0.6s to glide into place,
    strength >= 15;                             //   and this is real scrolling, not the faint end of a trackpad roll-out

  lastScrollTime = now;
  lastDirection = direction;
  lastStrength = strength;
  if (!paused && !turned && !pushedAgain && !keepGoing) return;  // still the same scroll: ignore

  // Not gliding right now? Then start from the section on screen
  // (in case the page was moved another way, like dragging the scrollbar).
  if (now - lastJumpTime > 1000) target = sectionOnScreen();

  // One section further, but never past the first or the last one
  target = Math.min(Math.max(target + direction, 0), sections.length - 1);
  sections[target].scrollIntoView({ behavior: "smooth" });  // glide there (changes course if already gliding)
  lastJumpTime = now;
}, { passive: false });  // "passive: false" is needed, or the browser won't let us stop the normal scrolling
