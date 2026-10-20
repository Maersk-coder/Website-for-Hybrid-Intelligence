# Website for Hybrid Intelligence

A website about **Hybrid Intelligence**: combining human creativity, ethics and contextual understanding with AI's scalability and efficiency.

> Work in progress. The site is built one section ("box") at a time, and most buttons are placeholders for now.

## How to view it

No installation needed. Open `Front Pages/Front_Page.html` in a web browser (double-click it).

## What's built so far

| Section | What it is |
|---|---|
| **Header** | Logo and the main menu (Manifesto, Tools & Frameworks, Research, Use Cases, Press, FAQ). It turns see-through over the animation. |
| **Page 1 – Animation section** | The opening screen: a 3D cloud of dots that changes shape, flowing background lines, and labels for the four levels: Individual, Workflow, Organization, Society & Economy. |
| **Page 2** | The next section. Being built now. |

Scrolling jumps one whole section at a time.

## How the folders are organised

```
Front Pages/
├── Front_Page.html          ← the website (one page, all sections)
├── General/                 ← used by the whole page
│   ├── CSS/                 ← base styles, buttons, header
│   └── JS/                  ← header behaviour, section-by-section scrolling
├── Page 1 (main)/           ← the animation section
│   ├── CSS/
│   ├── JS - Animations/     ← the dot cloud, lines, labels, changing word
│   └── How_the_animation_works.docx
└── Page 2/
    └── CSS/
```

Each new section gets its own `Page N` folder with `CSS` and `JS` inside.

## Chatbot

The `Chatbot/` folder holds a Python chatbot that answers questions about AI and Hybrid
Intelligence from a collection of research papers (it will appear on Page 3).
See [Chatbot/README.md](Chatbot/README.md). The research papers themselves are not uploaded,
because of copyright. They are listed in [Chatbot/papers/README.md](Chatbot/papers/README.md).

## Built with

- HTML, CSS and plain JavaScript (no frameworks)
- [Poppins](https://fonts.google.com/specimen/Poppins) font from Google Fonts

## Plans

- Finish Page 2 and the remaining sections
- Add a back end with **Python + Django**, for example so "Sign the Manifesto" saves signatures
