# files/: documents the website sends by email

The files in this folder are **not on GitHub**. They are only shared on request: ask the project
owner. Put them in this folder with exactly these names, and the website finds them by itself.

| File name | Used for |
|---|---|
| `Hybrid Intelligence Manifesto.pdf` | Attached to the "Thank you for signing" email (see `front_page/emails.py`) |
| `press.json` + the folder `press_images/` | The press stories and their pictures (from hi-infinity.ai/press). Load them with `python manage.py import_press` |
| `research.json` | The research publications (from hi-infinity.ai/research). Load them with `python manage.py import_research` |
| `use_cases.json` + the folder `use_case_images/` | The use cases and their pictures (from hi-infinity.ai/use-cases). Load them with `python manage.py import_use_cases` |
| The folder `manifesto_images/` | The diagrams and paper front pages on the three Manifesto pages (from hi-infinity.ai). Copy them into place with `python manage.py import_manifesto_images` |
| `faq.json` | The 80 FAQ questions and answers (from hi-infinity.ai/faq). Load them into the database with `python manage.py import_faq` |

If the file is missing, the email is still sent, just without the attachment, and the server
window shows a warning.
