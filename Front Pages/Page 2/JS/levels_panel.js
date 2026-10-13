// PAGE 2 · PANEL: pointing at a step shows that level in the panel under the staircase.
// Moving away again brings back the intro text (level "0").

(() => { // everything inside this "wrapper" is private to this file, so names can't clash with other scripts
    const zone = document.querySelector(".levels-zone");  // the staircase + panel
    const steps = zone.querySelectorAll(".step");  // the four steps of the staircase
    const parts = zone.querySelectorAll(".panel-part");  // the five panel parts (intro + 4 levels)

    // Show one part of the panel. "Level" is 0 for the intro, 1-4 for the four levels.
    function showPanelPart(level) {
        // the panel part with the same data-level as the level we want to show
        parts.forEach((part) => part.classList.toggle("is-shown", part.dataset.level == level));
        // Same for the steps: highlight the step that matches the level, unhighlight the others
        steps.forEach((step) => step.classList.toggle("is-active", step.dataset.level == level));
        //tells the CSS whether a step is chosen right now, so it can show the right text in the panel
        zone.classList.toggle("has-active", level !== "0");
    }

    // Pointing at a step (mouse), tabbing to it (keyboard) or tapping it (phone) shows its level   
     steps.forEach((step) => {
        step.addEventListener("mouseenter", () => showPanelPart(step.dataset.level));
        step.addEventListener("focus", () => showPanelPart(step.dataset.level));
        step.addEventListener("click", () => showPanelPart(step.dataset.level));
    });

    // Leaving the whole area (steps AND panel) brings the intro back.
    // So you can move the mouse down from a step to read the panel without it switching back.
    zone.addEventListener("mouseleave", () => showPanelPart("0"));
    zone.addEventListener("focusout", (event) => {
        if (!zone.contains(event.relatedTarget)) showPanelPart("0");  // if the new focus is outside the zone
    });
    
    document.addEventListener("click", (event) => {
        if (!zone.contains(event.target)) showPanelPart("0");  // if the click is outside the zone
    });



    
})();