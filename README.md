# Website for Hybrid Intelligence

A website about **Hybrid Intelligence**: combining human creativity, ethics and contextual understanding with AI's scalability and efficiency.

> Work in progress. The site is built one section ("box") at a time, and some buttons are placeholders for now.

## The two parts

The project consists of two programs (servers), each in its own folder:

| Folder | What it is | Built with | Address |
|---|---|---|---|
| [`hi_website/`](hi_website/README.md) | **The website.** Sends the pages to the browser, and (soon) saves the "Sign the Manifesto" and newsletter forms in a database. | Django (Python) | http://127.0.0.1:8001 |
| [`Chatbot/`](Chatbot/README.md) | **The chatbot** on Page 3. Answers questions about AI and Hybrid Intelligence from research papers. | FastAPI (Python) + Ollama | http://127.0.0.1:8000 |

The website page asks the chatbot server for answers. How the two talk to each other, and why each
uses its framework: [Chatbot/SERVER_AND_CLIENT.md](Chatbot/SERVER_AND_CLIENT.md).

## Starting everything

Three things must run at the same time. Each server runs in its own terminal window, and keeps
running as long as that window is open.

**1. Ollama** (the AI model). It starts by itself with Windows: check for the llama icon near the clock.
If it isn't there, start "Ollama" from the Start menu.

**2. The chatbot server** (FastAPI). In VS Code: *Terminal → New Terminal*, then:

```powershell
cd Chatbot
.\.venv\Scripts\Activate.ps1
python api.py
```

You see `(.venv)` at the start of the line after the second command. Wait until it says
`Uvicorn running on http://127.0.0.1:8000`.

**3. The website** (Django). Open **"Anaconda Prompt (miniconda3)"** from the Start menu, then:

```
cd "C:\Users\Thoma\OneDrive\Desktop\Hybrid Intelligence\hi_website"
python manage.py runserver 8001
```

Wait until it says `Starting development server at http://127.0.0.1:8001/`.

> **"Couldn't import Django"?** Then the chatbot's `(.venv)` is switched on in that window, and it has
> no Django. Type `deactivate` (the `(.venv)` disappears, `(base)` stays), then the command again.
> The VS Code terminal also works for Django this way: it must show `(base)` and **not** `(.venv)`.

**Then open http://127.0.0.1:8001 in the browser.**

**To stop:** press **Ctrl+C** in each of the two windows (Ollama can keep running).

| If you only start... | Then |
|---|---|
| the website (3) | The website works, but the chat on Page 3 says it can't reach the chatbot. |
| the chatbot (2) | Nothing to see in the browser: the website comes from Django. (The chatbot's own test page still works: http://127.0.0.1:8000/docs) |

**The first time** on a computer, both need to be set up once: the chatbot in
[Chatbot/README.md → Setup](Chatbot/README.md#setup-once), Django in
[hi_website/README.md → How Django was installed](hi_website/README.md#how-django-was-installed).

## What's built so far

| Section | What it is |
|---|---|
| **Header** | Logo and the main menu (Manifesto, Tools & Frameworks, Research, Use Cases, Press, FAQ). It turns see-through over the animation and hides on the last page. |
| **Page 1 – Animation section** | The opening screen: a 3D cloud of dots that changes shape, flowing background lines, and labels for the four levels: Individual, Workflow, Organization, Society & Economy. |
| **Page 2 – What is Hybrid Intelligence?** | The four levels as a staircase. Pointing at a level shows what it is about. |
| **Page 3 – Chatbot** | A chat panel in the middle of the page: ask questions about AI and Hybrid Intelligence, answered from research papers with sources. The mouse wheel scrolls the chat while the pointer is over it. |
| **Page 4 – The last section** | Newsletter, co-authors (a pop-up list) and contact information. |

Scrolling jumps one whole section at a time.

## How the folders are organised

```
Hybrid Intelligence/
├── README.md                    ← this file
├── hi_website/                  ← THE WEBSITE (Django), see hi_website/README.md
│   ├── manage.py
│   ├── config/                  ← the project's settings (settings.py, urls.py)
│   └── front_page/              ← the app: the front page and what its buttons do
│       ├── templates/
│       │   └── Front_Page.html  ← the website's HTML (one page, all sections)
│       └── static/              ← the CSS, JavaScript and images
│           ├── General/         ← used by the whole page
│           ├── Page 1 (main)/   ← the animation section
│           ├── Page 2/
│           ├── Page 3/
│           └── Page 4/
└── Chatbot/                     ← THE CHATBOT (FastAPI), see Chatbot/README.md
    ├── api.py                   ← the chatbot server
    ├── widget/                  ← the chat panel shown on Page 3
    └── ...
```

Each section has its own `Page N` folder with `CSS` and `JS` inside.

The research papers the chatbot uses are not uploaded, because of copyright. They are listed in
[Chatbot/papers/README.md](Chatbot/papers/README.md). The website's database (`hi_website/db.sqlite3`)
isn't uploaded either, because it will hold people's names and email addresses.

## Built with

- HTML, CSS and plain JavaScript, plus [Three.js](https://threejs.org/) for the 3D animation
- [Poppins](https://fonts.google.com/specimen/Poppins) font from Google Fonts
- [Django](https://www.djangoproject.com/) (Python) for the website server
- [FastAPI](https://fastapi.tiangolo.com/) (Python) and [Ollama](https://ollama.com/) for the chatbot

## Plans

- "Sign the Manifesto" and "Sign up for newsletter" save to the database (being built in `hi_website/`)
- Putting it online: [Chatbot/DEPLOYMENT.md](Chatbot/DEPLOYMENT.md)
