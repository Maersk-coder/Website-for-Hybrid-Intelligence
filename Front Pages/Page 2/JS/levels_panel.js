// PAGE 2 · PANEL: pointing at a step shows that level in the panel under the staircase.
// Moving away again brings back the intro text (level "0").

(() => { // everything inside this "wrapper" is private to this file, so names can't clash with other scripts
    const zone = document.querySelector(".levels-zone");  // the staircase + panel
    const stairs = zone.querySelector(".levels-stairs");  // the staircase (all four columns, up to the ground line)
    const steps = zone.querySelectorAll(".step");  // the four steps of the staircase
    const parts = zone.querySelectorAll(".panel-part");  // the five panel parts (intro + 4 levels)
    const panel = zone.querySelector(".levels-panel");  // the panel under the ground line
    let current = "0";  // the level shown right now ("0" = the intro)

    // Show one part of the panel. "Level" is 0 for the intro, 1-4 for the four levels.
    function showPanelPart(level) {
        if (level === current) return;  // already showing it: nothing to do
        current = level;
        // the panel part with the same data-level as the level we want to show
        parts.forEach((part) => part.classList.toggle("is-shown", part.dataset.level == level));
        // Same for the steps: highlight the step that matches the level, unhighlight the others
        steps.forEach((step) => step.classList.toggle("is-active", step.dataset.level == level));
        //tells the CSS whether a step is chosen right now, so it can show the right text in the panel
        zone.classList.toggle("has-active", level !== "0");
    }

    // Which step is under the mouse? Each step owns its WHOLE column, from the top of the staircase
    // down to the ground line (also the empty space above the shorter steps, and the gaps between them).
    function stepUnder(mouseX) {
        const box = stairs.getBoundingClientRect();  // where the staircase is on the screen
        const column = Math.floor(((mouseX - box.left) / box.width) * steps.length);  // 0, 1, 2 or 3
        return steps[Math.min(Math.max(column, 0), steps.length - 1)];  // never outside 0-3
    }

    // Moving the mouse anywhere over the staircase picks the step in that column, instantly
    stairs.addEventListener("mousemove", (event) => showPanelPart(stepUnder(event.clientX).dataset.level));

    // Leaving the staircase: down into the panel keeps the level (so it can be read), anywhere else shows the intro
    stairs.addEventListener("mouseleave", (event) => {
        if (!panel.contains(event.relatedTarget)) showPanelPart("0");
    });

    // Leaving the panel too (the whole area) brings the intro back
    zone.addEventListener("mouseleave", () => showPanelPart("0"));

    // Keyboard (tabbing to a step) and phones (tapping a step)
    steps.forEach((step) => {
        step.addEventListener("focus", () => showPanelPart(step.dataset.level));
        step.addEventListener("click", () => showPanelPart(step.dataset.level));
    });
    zone.addEventListener("focusout", (event) => {
        if (!zone.contains(event.relatedTarget)) showPanelPart("0");  // if the new focus is outside the zone
    });
    document.addEventListener("click", (event) => {
        if (!zone.contains(event.target)) showPanelPart("0");  // if the click is outside the zone
    });
})();
