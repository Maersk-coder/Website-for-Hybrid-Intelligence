// FEATURED USE CASE: the card at the bottom right of Page 1 shows the Iconic use cases one after the other.
// It changes at the same moment as the word under the title: animation.js sends a "shape-change" signal
// each time the dot cloud starts changing shape, and this script listens for it.
// The list of use cases comes from the database: home() in views.py puts it in the page as "featured-cases".

(() => {
  const data = document.getElementById("featured-cases");
  const card = document.querySelector(".animation-card");
  if (!data || !card) return;

  const cases = JSON.parse(data.textContent);       // [{organisation: "Ikea", title: "..."}, ...]
  if (cases.length < 2) return;                     // nothing to switch between

  const title = card.querySelector(".card-title");
  const text = card.querySelector(".card-text");
  let index = 0;

  document.addEventListener("shape-change", () => {
    index = (index + 1) % cases.length;             // the next one, and back to the first after the last
    card.classList.add("is-swapping");              // fade the old text out (animation_card.css)
    setTimeout(() => {
      title.textContent = cases[index].organisation;
      text.textContent = cases[index].title;
      card.classList.remove("is-swapping");         // and the new text in
    }, 400);
  });
})();
