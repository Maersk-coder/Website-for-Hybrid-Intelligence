// Header is transparent over the animation section and turns solid once the page is scrolled.
(() => {
  const header = document.querySelector(".site-header");
  const update = () => header.classList.toggle("scrolled", window.scrollY > 10);
  window.addEventListener("scroll", update, { passive: true });
  update();
})();



