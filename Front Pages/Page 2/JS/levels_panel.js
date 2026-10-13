// PAGE 2 · PANEL: pointing at a step shows that level in the panel under the staircase.
// Moving away again brings back the intro text (level "0").

(() => { // everything inside this "wrapper" is private to this file, so names can't clash with other scripts
    const zone = document.querySelector(".levels-zone");  // the staircase + panel
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

    // Every time the mouse moves onto something new inside the staircase + panel area:
    zone.addEventListener("mouseover", (event) => {
        const step = event.target.closest(".step");  // the step the mouse is on (or null if it's not on a step)
        if (step) {
            showPanelPart(step.dataset.level);  // on a step: show its level
        } else if (!panel.contains(event.target)) {
            showPanelPart("0");  // the empty space above the steps: back to the intro
        }
        // in the panel: keep showing what's shown, so it can be read
    });

    // Leaving the whole area (steps AND panel) brings the intro back
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
