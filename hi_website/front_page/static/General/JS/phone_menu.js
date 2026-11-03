// PHONE MENU: opens and closes the full-screen menu on small screens (the look is in phone_menu.css).

const phoneMenu = document.getElementById("phone-menu");       // the menu itself (the <dialog>)
const menuOpenButton = document.getElementById("menu-open");    // the ☰ button in the header
const menuCloseButton = document.getElementById("menu-close");  // the ✕ button in the menu

// ☰ opens the menu. showModal() also makes the page behind it unclickable, and lets Esc close it.
menuOpenButton.addEventListener("click", () => phoneMenu.showModal());

// ✕ closes it
menuCloseButton.addEventListener("click", () => phoneMenu.close());

// Tapping a link or the button in the menu closes it too
phoneMenu.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => phoneMenu.close());
});

// If the screen gets wider than 800px while the menu is open (e.g. a tablet turned sideways),
// close it, because the normal menu bar is back.
window.matchMedia("(min-width: 801px)").addEventListener("change", (event) => {
  if (event.matches) phoneMenu.close();
});
