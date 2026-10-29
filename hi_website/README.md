# hi_website: the website, run by Django

This folder is the **Django project**: the program that sends the Hybrid Intelligence website to the
visitor's browser, and (soon) saves the "Sign the Manifesto" and newsletter forms in a database.

It is built the way the CS-320 slides do it (the "football" example): a **project** (`hi_website`) with
one **app** (`front_page`).

The chatbot on Page 3 is **not** part of Django: it is its own server in `../Chatbot/`.
How to start both: see [Starting everything](../README.md#starting-everything) in the main README.

## How to start it

Open **"Anaconda Prompt (miniconda3)"** from the Start menu (Django is installed there) and type:

```
cd "C:\Users\Thoma\OneDrive\Desktop\Hybrid Intelligence\hi_website"
python manage.py runserver 8001
```

Then open **http://127.0.0.1:8001** in the browser. Leave the window open: the website runs as
long as it is open. Stop it with **Ctrl+C**.

> **"Couldn't import Django"?** Then the chatbot's `(.venv)` is switched on in that window, and it has
> no Django. Type `deactivate` (the `(.venv)` disappears, `(base)` stays), then the command again.
> The VS Code terminal also works for Django this way: it must show `(base)` and **not** `(.venv)`.

**Why 8001?** Django normally uses port 8000, but the chatbot server already uses 8000.
Two servers can't share one port, so Django gets 8001.

## The folders

```
hi_website/
├── manage.py              Django's tool. You use it by typing: python manage.py <command>
├── db.sqlite3             The database. Not on GitHub: it holds people's names and emails.
├── config/                The settings for the whole project ("config" = configuration)
│   ├── settings.py        All settings, e.g. the list of apps (INSTALLED_APPS)
│   ├── urls.py            Which address goes to which app
│   ├── wsgi.py, asgi.py   Technical files for going online. Don't change them.
│   └── __init__.py        Tells Python this folder is a package. Leave it empty.
└── front_page/            The app: the front page and what its buttons do
    ├── templates/
    │   └── Front_Page.html    The website's HTML (all sections in one page)
    ├── static/                The website's CSS, JavaScript and images
    │   ├── General/           Used by the whole page (base styles, buttons, header, scrolling)
    │   ├── Page 1 (main)/     The animation section
    │   ├── Page 2/            "What is Hybrid Intelligence?" (the four levels)
    │   ├── Page 3/            The chatbot section
    │   └── Page 4/            The last section (newsletter, co-authors, contact)
    ├── views.py           The functions that answer a visit, e.g. "send the front page"
    ├── urls.py            Which address goes to which function in views.py (made in stage 2)
    ├── models.py          The database tables, written as Python classes (stage 3)
    ├── admin.py           Which tables can be seen and edited at /admin (stage 3)
    ├── migrations/        Made by Django: the steps that build the tables in the database
    ├── apps.py            The app's name. Made by Django
    └── tests.py           For automatic tests. Not used yet
```

### Why these names?

- **`templates`** and **`static`** are names Django looks for by itself, so they can't easily be changed.
  - A **template** is an HTML page with blanks, like a form letter ("Dear {{ name }}"). Django fills in
    the blanks before sending it, e.g. `{{ count }}` → "123 people have signed".
  - **Static** files are sent unchanged: they are the same for every visitor (CSS, JavaScript, images).
- **`config`**: Django first named this folder after the project (`hi_website/hi_website/`, like
  `football_project/football_project/` in the slides). It was renamed to `config` to say what it holds.
  The new name is written in `manage.py`, `config/settings.py`, `config/wsgi.py` and `config/asgi.py`.
- **Project and app** (slides 03, p. 8): the *project* (`hi_website`) has its settings in `config/`. An *app* is one
  part of the website with one job. Here there's one app, `front_page`. A login would get its own
  app later (e.g. `users`, as in slides 06).

## What happens when someone visits (slides 03, p. 11–14: "MTV")

```
Browser asks for http://127.0.0.1:8001/
   → config/urls.py and front_page/urls.py: which function handles this address?
   → front_page/views.py: the function runs (and fetches data from the database via models.py if needed)
   → front_page/templates/Front_Page.html: the blanks are filled in
   → the finished page goes back to the browser, which then fetches the CSS/JS/images from static/
```

Django calls this **M**odel (`models.py`), **T**emplate (`templates/`), **V**iew (`views.py`).

## Commands

All typed in the Anaconda Prompt, inside this folder:

| Command | What it does |
|---|---|
| `python manage.py runserver 8001` | Starts the website on http://127.0.0.1:8001 |
| `python manage.py makemigrations` | After changing `models.py`: prepares the change for the database |
| `python manage.py migrate` | Carries the prepared changes out in the database (`db.sqlite3`) |
| `python manage.py createsuperuser` | Makes an admin account for http://127.0.0.1:8001/admin |
| `python manage.py shell` | A Python prompt with access to the database, to try things out |

## How Django was installed

With conda, as in the slides (Django 6.1.2, in Miniconda's main environment):

```
conda install -c anaconda django
python -m django version
```

On another computer: install [Miniconda](https://www.anaconda.com/download), run the first command
in the Anaconda Prompt, then `python manage.py migrate` in this folder to make a new, empty database.

## Building it, stage by stage

| Stage | What | Slides |
|---|---|---|
| 1 | Install Django, create the project and the app, create the database | 03, p. 3–10 |
| 2 | The front page sent by Django (view, urls, static files) | 04, p. 3–11 |
| 3 | Tables for signatures and newsletter subscribers, and the admin site | 04, p. 12–18 |
| 4 | The "Sign the Manifesto" form (with a newsletter checkbox) and the newsletter form | 05 |
| 5 | Show data on the page, e.g. how many people have signed | 04, p. 19–22 |

A login (slides 06) is not planned for now.

**Status:** stages 1 and 2 are done; next is stage 3.
