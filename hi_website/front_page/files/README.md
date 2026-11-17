# files/: documents the website sends by email

The files in this folder are **not on GitHub**. They are only shared on request: ask the project
owner. Put them in this folder with exactly these names, and the website finds them by itself.

| File name | Used for |
|---|---|
| `Hybrid Intelligence Manifesto.pdf` | Attached to the "Thank you for signing" email (see `front_page/emails.py`) |
| `faq.json` | The 80 FAQ questions and answers (from hi-infinity.ai/faq). Load them into the database with `python manage.py import_faq` |

If the file is missing, the email is still sent, just without the attachment, and the server
window shows a warning.
