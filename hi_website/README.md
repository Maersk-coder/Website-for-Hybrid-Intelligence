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
├── .env                   Your private settings: the email account and its App password. Not on GitHub
├── .env.example           Shows what goes in .env (copy it to .env on a new computer)
├── media/                 Uploaded pictures (the press stories'). Not on GitHub
├── sent_emails/          When .env has no email account, emails are saved here as .log files instead of being sent. Not on GitHub
├── How_Django_works.docx  A simple explanation: Model, View, Controller, and how Django works
├── config/                The settings for the whole project ("config" = configuration)
│   ├── settings.py        All settings, e.g. the list of apps (INSTALLED_APPS)
│   ├── urls.py            Which address goes to which app
│   ├── wsgi.py, asgi.py   Technical files for going online. Don't change them.
│   └── __init__.py        Tells Python this folder is a package. Leave it empty.
└── front_page/            The app: the front page and what its buttons do
    ├── templates/
    │   ├── Front_Page.html          The website's HTML (all sections in one page)
    │   ├── header.html              The menu bar and phone menu, shared by all pages ({% include 'header.html' %})
    │   ├── footer.html              Page 4, the end of every page (contact, newsletter, co-authors) ({% include 'footer.html' %})
    │   ├── buttons/                 The pages opened from a menu button ("_bt" = button page):
    │   │   ├── manifesto/           The three pages in the Manifesto dropdown (one folder, to keep them together):
    │   │   │   ├── Manifesto_bt.html            The Hybrid Intelligence Manifesto (/manifesto/), with the signature count
    │   │   │   ├── ECON_Manifesto_bt.html       ECON Manifesto: The Economics of HI (/manifesto/economics/)
    │   │   │   ├── Education_Manifesto_bt.html  Education Manifesto (/manifesto/education/), with the Educational use cases
    │   │   │   └── manifesto_series.html        The three pages as cards, at the end of each of them
    │   │   ├── FAQ_bt.html          The FAQ page (/faq/): 80 questions in 8 categories, from the database
    │   │   ├── Press_bt.html        The Press page (/press/): the news stories as cards, from the database
    │   │   ├── Research_bt.html     The Research page (/research/): the publications, from the database
    │   │   ├── Use_Cases_bt.html    The Use Cases page (/use-cases/): the use cases as cards, with filter buttons
    │   │   └── publication_authors.html   The authors of one publication ("+ N more"), used by Research_bt.html
    │   ├── Share_Research.html      The "Share your research" form (/research/share/)
    │   ├── Share_Use_Case.html      The "Share your use case" form (/use-cases/share/)
    │   ├── Sign_The_Manifesto.html  The page with the "Sign the Manifesto" form (/sign/)
    │   ├── Newsletter.html          The page with the "Sign up for newsletter" form (/newsletter/)
    │   ├── Unsubscribe.html         The page behind the "Unsubscribe" link in every newsletter
    │   └── Thank_You.html           Shown after a form is sent (/thanks/)
    ├── static/                The website's CSS, JavaScript and images
    │   ├── General/           Used by the whole page (base styles, buttons, header, scrolling)
    │   ├── Page 1 (main)/     The animation section
    │   ├── Page 2/            "What is Hybrid Intelligence?" (the four levels)
    │   ├── Page 3/            The chatbot section
    │   ├── Page 4/            The last section (newsletter, co-authors, contact)
    │   └── Buttons/           The pages opened from a menu button (FAQ, Press, Research, Use Cases, Manifesto):
    │       ├── CSS/               faq.css, press.css, research.css, use_cases.css
    │       ├── JS/                faq_contents.js (marks the current theme in the FAQ guide)
    │       └── Manifesto/         The three Manifesto pages: CSS/manifesto.css and JS/manifesto_contents.js (the Contents guide)
    ├── views.py           The functions that answer a visit: home, sign and newsletter (GET shows the form, POST saves it), thanks
    ├── urls.py            Which address goes to which function in views.py: /, /sign/, /newsletter/, /thanks/
    ├── forms.py           The forms visitors fill in, built from the tables (SignatureForm, SubscriberForm)
    ├── emails.py          The emails: "Thank you for signing" (with the PDF), the newsletter welcome, the monthly issues
    ├── management/commands/send_newsletter.py   The monthly command: python manage.py send_newsletter
    ├── management/commands/import_faq.py        Loads the FAQ from files/faq.json: python manage.py import_faq
    ├── management/commands/import_press.py      Loads the press stories and pictures: python manage.py import_press
    ├── management/commands/import_research.py   Loads the publications from files/research.json: python manage.py import_research
    ├── management/commands/import_use_cases.py  Loads the use cases and pictures: python manage.py import_use_cases
    ├── management/commands/import_manifesto_images.py  Copies the Manifesto pages' pictures: python manage.py import_manifesto_images
    ├── files/             The documents the emails send (the manifesto PDF). Not on GitHub: see files/README.md
    ├── models.py          The database tables, written as Python classes: Signature, Subscriber, Newsletter, FaqCategory, FaqQuestion, PressArticle, Publication, ResearchSubmission, UseCase and UseCaseSubmission
    ├── admin.py           Which tables can be seen and edited at /admin
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

## The Manifesto pages (the dropdown)

Point at **Manifesto** in the menu bar and a panel with three pages appears (clicking "Manifesto" opens the first).
On phones, tap **Manifesto** in the ☰ menu and the three pages fold out under it. The dropdown is in `header.html`,
its look at the end of `General/CSS/header.css` (and `phone_menu.css`).

| Page | Address | From the database |
|---|---|---|
| The Hybrid Intelligence Manifesto | /manifesto/ | How many have signed (`Signature`) |
| ECON Manifesto: The Economics of Hybrid Intelligence | /manifesto/economics/ | nothing |
| Education Manifesto: Hybrid Intelligence in Education | /manifesto/education/ | The Educational use cases (`UseCase`) |

- **The text** (from hi-infinity.ai) is written straight into the templates in `templates/buttons/manifesto/`,
  because it is long prose that rarely changes. To change a sentence, edit the template.
- **The pictures** (diagrams and paper front pages) are not on GitHub. Put the folder `manifesto_images/` in
  `front_page/files/` and run `python manage.py import_manifesto_images`: it copies them into `media/manifesto/`.
- **The full papers:** the main Manifesto PDF is emailed to people who sign; the ECON and Education papers link to
  the PDFs on hi-infinity.ai.

## The Use Cases page

**http://127.0.0.1:8001/use-cases/** (the "Use Cases" link in the menu). The 29 use cases from
hi-infinity.ai/use-cases are in the table `UseCase`: organisation, title, type (Partner, Iconic, Contributed,
Educational), link and a picture.

- **The filter buttons** (All, Partner, Iconic, ...) add `?type=iconic` to the address: a GET request with a
  "query string". `use_cases()` in `views.py` reads it with `request.GET.get('type')` and shows only that type.
- **First time on a computer:** put `use_cases.json` and `use_case_images/` in `front_page/files/` and run
  `python manage.py import_use_cases`.
- **A new use case:** admin site → **Use cases** → **+ Add**, with a picture.
- **"Share your use case"** opens our own form (`/use-cases/share/`): saved under **Use case submissions** and
  emailed to the contact address, like "Share your research".

## The Research page

**http://127.0.0.1:8001/research/** (the "Research" link in the menu). The 16 publications from
hi-infinity.ai/research are in the table `Publication`: title, date (as text, e.g. "October 2026"),
summary, authors and a link. `order` sets the place: number 1 is shown first, as "Latest".

- **First time on a computer:** put `research.json` in `front_page/files/` and run `python manage.py import_research`.
- **A new publication:** admin site → **Publications** → **+ Add**. Give it order 1 (and move the others down
  in the list, where the order can be changed directly) to show it as "Latest".
- **"Share your research"** opens our own form (`/research/share/`). Each submission is saved in the admin site
  under **Research submissions**, and emailed to the contact address (`CONTACT_EMAIL` in settings, the site's
  Gmail). "Reply" in the mail program answers the person who shared it.
- "Read more" opens the publication on hi-infinity.ai (this site has no pages for single publications yet).

## The Press page

**http://127.0.0.1:8001/press/** (the "Press" link in the menu). The news stories about Hybrid
Intelligence (from hi-infinity.ai/press) are in the table `PressArticle`: title, outlet, date, summary,
link to the article, and a picture. "Read More" opens the article on the newspaper's own website.

- **First time on a computer:** put `press.json` and the folder `press_images/` in `front_page/files/` and
  run `python manage.py import_press`. It copies the pictures into `media/press/`.
- **A new story:** admin site → **Press articles** → **+ Add**: fill in the fields and upload a picture.
- The pictures belong to the newspapers, so `media/` and `front_page/files/` are not on GitHub.
- Uploading pictures needs Pillow: `conda install -c anaconda pillow` (installed).

All button pages (FAQ, Press, ...) share the background with the faint lines and the page heading
(small indigo line, big title with a highlighted part, numbers from the database that count up, a row of
small buttons, and thin blueprint lines): `General/CSS/button_page.css` and `General/JS/count_up.js`.
They end with Page 4 (`footer.html`). The numbers are counted in `faq()` and `press()` in `views.py`.

## The FAQ page

**http://127.0.0.1:8001/faq/** (the "FAQ" link in the menu). The 80 questions and answers come from
hi-infinity.ai/faq and live in the database, in two linked tables: `FaqCategory` (8 categories) and
`FaqQuestion` (each question belongs to one category through a ForeignKey).

- **First time on a computer:** put `faq.json` in `front_page/files/` and run `python manage.py import_faq`.
- **Editing:** admin site → **FAQ categories** → open a category to edit all its questions at once, or
  **FAQ questions** for one list of all 80 with a search box.
- Six answers link to pages on hi-infinity.ai that this site doesn't have yet; for now they are plain text.

## The monthly newsletter

**Writing an issue:** http://127.0.0.1:8001/admin/ → **Newsletters** → **+ Add**. Write a subject and the
text (what is going on in Hybrid Intelligence this month) and click **Save**. It is not sent yet: the
**Sent at** column stays empty.

**Sending it:**
- **Right away (for testing):** in the Newsletters list, tick the issue, choose **"Send to all
  subscribers now"** in the Action menu and click **Go**.
- **Every month (automatic):** the command `python manage.py send_newsletter` sends the next issue that
  hasn't been sent yet, to everyone on the list. Running it twice never sends twice.

**What subscribers get:**
- When they sign up (on Page 4, or with the box when signing the manifesto): a welcome email, and in a
  separate email the newest issue that has been sent.
- Every newsletter has a personal **Unsubscribe** link at the bottom (EU rules). It opens a page with a
  button that takes them off the list.

**Real emails:** when `.env` has an email account, these are really sent, to everyone on the list. To
test safely, make sure only your own test addresses are on the list (admin → Subscribers).

### Running it every month on Windows (Task Scheduler)

Django only reacts when someone visits a page, so it can't do something "every month" by itself.
Windows can run the command for it:

1. Start menu → **Task Scheduler** ("Opgaveplanlægning") → **Create Basic Task**.
2. Name: `Hybrid Intelligence newsletter`. Trigger: **Monthly**, e.g. day 1 at 10:00.
3. Action: **Start a program**:
   - Program: `C:\Users\Thoma\miniconda3\python.exe`
   - Arguments: `manage.py send_newsletter`
   - Start in: `C:\Users\Thoma\OneDrive\Desktop\Hybrid Intelligence\hi_website`
4. **Finish**. The computer has to be on at that time.

When the website is online, the server does this instead (with its own timer, e.g. "cron").

## Commands

All typed in the Anaconda Prompt, inside this folder:

| Command | What it does |
|---|---|
| `python manage.py runserver 8001` | Starts the website on http://127.0.0.1:8001 |
| `python manage.py makemigrations` | After changing `models.py`: prepares the change for the database |
| `python manage.py migrate` | Carries the prepared changes out in the database (`db.sqlite3`) |
| `python manage.py createsuperuser` | Makes an admin account for http://127.0.0.1:8001/admin |
| `python manage.py import_manifesto_images` | Copies the Manifesto pages' pictures from `front_page/files/manifesto_images/` into `media/manifesto/` |
| `python manage.py import_use_cases` | Loads the use cases and pictures from `front_page/files/` (replaces the current ones) |
| `python manage.py import_research` | Loads the research publications from `front_page/files/research.json` (replaces the current ones) |
| `python manage.py import_press` | Loads the press stories and pictures from `front_page/files/` (replaces the current ones) |
| `python manage.py import_faq` | Loads the FAQ questions from `front_page/files/faq.json` (replaces the current FAQ) |
| `python manage.py send_newsletter` | Sends the next unsent newsletter issue to all subscribers |
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

**Status:** stages 1–3 are done. Stage 4: "Sign the Manifesto" works (/sign/): one signature per email, and a thank-you email with the manifesto attached (saved as a file while testing). The newsletter form works too (/newsletter/, the button on Page 4), with a welcome email. Emails are really sent when .env has an email account (see .env.example), otherwise saved as files.
