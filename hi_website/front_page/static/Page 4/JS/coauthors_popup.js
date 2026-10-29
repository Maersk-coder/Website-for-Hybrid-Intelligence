// PAGE 4 · CO-AUTHORS POP-UP: fills the list with the names, opens it with the "Co-authors" button,
// and closes it with the X, the Esc key, or a click anywhere outside the white box.
// The names come from coauthors_list.js (made by Python from Data/coauthors.csv).

(() => {  // the "wrapper" that keeps these names private to this file
  const popup = document.getElementById("coauthors");             // the <dialog>
  const openButton = document.getElementById("coauthors-open");   // the "Co-authors" button on Page 4
  const closeButton = document.getElementById("coauthors-close"); // the X
  const list = document.getElementById("coauthors-list");         // the empty <ul>

  // 1. Fill the list: one <li> per co-author, with a <span> for the name, the title and the place
  COAUTHORS.forEach((person) => {
    const item = document.createElement("li");         // make a new, empty <li>
    ["name", "role", "place"].forEach((part) => {
      const span = document.createElement("span");      // make a new <span>
      span.className = "coauthor-" + part;              // e.g. "coauthor-name", so the CSS can style it
      span.textContent = person[part];                  // the text, e.g. "Jacob Sherson"
      item.append(span);                                // put the <span> inside the <li>
    });
    list.append(item);                                  // put the finished <li> in the list
  });

  // 2. Open: the browser shows the <dialog> on top of everything and dims the page behind it
  openButton.addEventListener("click", () => popup.showModal());

  // 3. Close with the X
  closeButton.addEventListener("click", () => popup.close());

  // 4. Close with a click outside the white box.
  //    The <dialog> is exactly as big as the box, so a click that lands on the dialog ITSELF
  //    (not on the box or anything inside it) can only be a click on the dimmed page around it.
  popup.addEventListener("click", (event) => {
    if (event.target === popup) popup.close();
  });

})();
