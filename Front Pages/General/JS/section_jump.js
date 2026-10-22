// SECTION JUMP: one scroll of the mouse wheel = glide to the next (or previous) section.
// Scrolling again while it glides changes course right away, so fast scrolling never waits.

const sections = document.querySelectorAll("section");  // every section on the page, top to bottom
let target = 0;          // the section we are on, or gliding to
let lastScrollTime = 0;  // when the wheel last moved
let lastDirection = 0;   // 1 = last scroll was down, -1 = up
let lastJumpTime = 0;    // when the last jump started
let signals = [];        // the scroll signals of the last 0.3 seconds, as [time, strength], oldest first

// How strong the scrolling was between "from" and "to" milliseconds ago: all signals in that time added up.
// (Adding them up over time, instead of looking at single signals, also works when a busy page hands over
//  several signals bundled into one big one: the total over 0.1 seconds stays the same.)
function strengthBetween(now, from, to) {
  return signals
    .filter(([time]) => now - time < from && now - time >= to)
    .reduce((total, [, strength]) => total + strength, 0);
}

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
  if (document.querySelector("dialog[open]")) return; // a pop-up is open: let the wheel scroll the pop-up, not jump between pages

  // The mouse is over the chat panel (Page 3): the wheel scrolls the chat (the messages, or the start screen
  // on a short screen), never jumps between pages. Where there is nothing to scroll (the top bar, the question
  // box, or already at the end), the wheel does nothing. To jump to another page, move the mouse off the panel.
  if (event.target.closest(".hi-chat")) {
    const area = event.target.closest(".hi-chat-messages, .hi-chat-start");
    const canScroll = area && (event.deltaY > 0
      ? area.scrollTop + area.clientHeight < area.scrollHeight - 1   // room to scroll down
      : area.scrollTop > 0);                                         // room to scroll up
    if (!canScroll) event.preventDefault();
    return;
  }

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
  const turned = direction !== lastDirection;   // it turned the other way

  // Remember this signal, and forget the ones older than 0.3 seconds (or from before turning around).
  if (turned) signals = [];
  signals.push([now, strength]);
  signals = signals.filter(([time]) => now - time < 300);

  // Is the scrolling fading out? A trackpad keeps sending weaker and weaker signals for about a second
  // after you let go: the old scroll "rolling out". A mouse wheel, or fingers still moving on the pad,
  // stay as strong or get stronger. So: compare the last 0.1 s with the 0.2 s before it (per 0.1 s).
  const recentSpeed = strengthBetween(now, 100, 0);
  const earlierSpeed = strengthBetween(now, 300, 100) / 2;
  const fading = recentSpeed < earlierSpeed * 0.7;

  // Does this scroll signal start a new jump?
  const paused = now - lastScrollTime > 60;     // the wheel was still for a moment
  const pushedAgain =                           // a new swipe while the old one is still rolling out:
    recentSpeed > earlierSpeed * 2 &&           //   the scrolling suddenly gets twice as strong,
    recentSpeed > 40 &&                         //   it's a real push, not a tiny wobble,
    now - lastJumpTime > 300;                   //   and the last jump didn't JUST start (a swipe starts weak and builds up)
  const keepGoing =                             // still scrolling after the last glide has finished:
    now - lastJumpTime > 600 &&                 //   the last jump had 0.6s to glide into place,
    strength >= 15;                             //   and this is real scrolling, not a tiny wobble

  lastScrollTime = now;
  lastDirection = direction;
  if (!turned && fading) return;                                 // a trackpad rolling out: never a new jump
  if (!paused && !turned && !pushedAgain && !keepGoing) return;  // still the same scroll: ignore

  // Not gliding right now? Then start from the section on screen
  // (in case the page was moved another way, like dragging the scrollbar).
  if (now - lastJumpTime > 1000) target = sectionOnScreen();

  // One section further, but never past the first or the last one
  target = Math.min(Math.max(target + direction, 0), sections.length - 1);
  sections[target].scrollIntoView({ behavior: "smooth" });  // glide there (changes course if already gliding)
  lastJumpTime = now;
}, { passive: false });  // "passive: false" is needed, or the browser won't let us stop the normal scrolling
