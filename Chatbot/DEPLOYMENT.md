# Putting the website and the chatbot online

Two servers have to go online:

1. **The website** (`hi_website/`, Django). It sends the pages and saves the forms in its database.
   Because it runs Python, it needs a computer that can run Python. A free file host like GitHub
   Pages can't do that any more (it could while the website was only HTML, CSS and JavaScript files).
2. **The chatbot server** (`Chatbot/api.py` + Ollama + the search index). This is the hard part,
   because the AI model needs a lot of memory and works best with a graphics card.

## The three routes for the chatbot server

| Route | How it works | Cost | Downside |
|---|---|---|---|
| **A. Your own laptop + a tunnel** | `api.py` and Ollama keep running on your laptop. A free "tunnel" (Cloudflare) gives it a public `https://` address. | Free | The chat only works while your laptop is on, awake, and running Ollama, `api.py` and the tunnel. One question at a time. |
| **B. A rented server** | `api.py` and Ollama run on a rented computer in a data centre (e.g. Hetzner). | ~€10–20 a month | Without a graphics card, answers are even slower than on your laptop. A server with a graphics card costs much more. |
| **C. A paid AI model + free hosting** | Claude (Anthropic) writes the answers; `api.py` runs on a free host like Render. | Hosting free, ~0.1–5 cents per question | The Claude option has to be put back (it's saved in Git, commit `0145a3c`). |

Free hosts like Render and Railway can't run Ollama: they have too little memory (about 0.5 GB,
the model needs about 4 GB) and no graphics card.

**Wherever the server runs, the PDFs and the search index must be there too.** They're not on
GitHub (copyright), so for route B or C they must be copied over by hand, or the index rebuilt there
with `python ingest.py`. For route A they're already on your laptop.

**The website (Django)** can go the same way as the chatbot: on your laptop with a tunnel (route A,
below), or on a host that runs Django, e.g. PythonAnywhere (has a free plan) or a rented server.
Its database (`db.sqlite3`) is not on GitHub (it holds personal data), so a new one is made there
with `python manage.py migrate`.

The rest of this file explains **route A for both**, step by step: everything runs on your laptop.

---

## Route A, step by step

### Step 1: Install Cloudflare's tunnel program (once)

In a terminal:

```powershell
winget install --id Cloudflare.cloudflared
```

Close the terminal and open a new one, so Windows finds the new program.

### Step 2: Start everything

1. **Ollama, the chatbot and the website**, exactly as in
   [Starting everything](../README.md#starting-everything) in the main README.
2. **A tunnel for the chatbot**, in a new terminal:
   ```powershell
   cloudflared tunnel --url http://127.0.0.1:8000
   ```
3. **A tunnel for the website**, in one more terminal:
   ```powershell
   cloudflared tunnel --url http://127.0.0.1:8001
   ```

After a few seconds, each tunnel prints an address like `https://some-random-words.trycloudflare.com`.
Write down which one is the **chatbot's** and which one is the **website's**.

Check the chatbot's: open `https://<the chatbot's address>/health` in the browser. You should see `"status":"ok"`.

### Step 3: Tell the website and the chatbot about each other

**The page must know the chatbot's address.** In
`hi_website/front_page/templates/Front_Page.html`, near the bottom, change `data-api` to the
chatbot tunnel's address (no `/` at the end):

```html
<script src="{% static 'chat-widget.js' %}" data-api="https://<the chatbot's address>" data-target="#hi-chat"></script>
```

**The chatbot must allow the website.** In `Chatbot/.env`, add the website tunnel's address to
`ALLOWED_ORIGINS` (keep the local ones if you still want to test on your own computer):

```
ALLOWED_ORIGINS=https://<the website's address>,http://127.0.0.1:8001,http://localhost:8001
```

**Django must accept the tunnel's address.** In `hi_website/config/settings.py`:

```python
DEBUG = False                                        # don't show error details to visitors
ALLOWED_HOSTS = ['.trycloudflare.com', '127.0.0.1', 'localhost']
CSRF_TRUSTED_ORIGINS = ['https://*.trycloudflare.com']   # so the forms can be sent through the tunnel
```

- `ALLOWED_HOSTS`: Django only answers visits to these addresses. The dot in front means "any
  address ending in trycloudflare.com".
- `CSRF_TRUSTED_ORIGINS`: the forms' security check (`{% csrf_token %}`) must know the tunnel's
  `https://` address, otherwise sending a form gives an error 403.
- `DEBUG = False`: with `True`, an error shows visitors parts of your code and settings.

Then restart both servers (Ctrl+C, then the start command again): `.env` and `settings.py` are only
read at the start. With `DEBUG = False`, start the website with
`python manage.py runserver 8001 --insecure`, otherwise Django stops sending the CSS, JavaScript and
images (see "Good to know").

Open the website tunnel's address, scroll to Page 3 and ask a question.

### Important: the tunnel addresses change

The free "quick tunnel" gets a **new random address every time** you start `cloudflared`. Each
time, step 3 must be done again for the new addresses (`data-api` and `ALLOWED_ORIGINS`; the Django
settings already accept any `trycloudflare.com` address). Cloudflare also says quick tunnels are meant
for testing, not for a permanent website.

For a **permanent address**: create a free Cloudflare account, buy a domain name (about €10 a year,
e.g. `hybrid-intelligence.com`) and set up a *named tunnel* for it
([Cloudflare's guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/)).
The addresses then stay the same, and step 3 is done only once (with your own domain in
`ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` and `ALLOWED_ORIGINS`).

---

## Checklist before going online

- [ ] `,null` is removed from `ALLOWED_ORIGINS` in `Chatbot/.env`.
- [ ] `ALLOWED_ORIGINS` contains the website's public address.
- [ ] `data-api` in `Front_Page.html` is the chatbot's public address.
- [ ] Django: `DEBUG = False`, and `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are set (step 3).
- [ ] Django: the admin account has a **strong password**. The admin page (`/admin`) is public too,
      and shows everyone's names and emails. (The slides use the password `123`: fine on your own
      computer, never online.)
- [ ] Django: `SECRET_KEY` in `settings.py` is replaced by a new, secret one. The one there now is
      public on GitHub. For a real site, keep it in a file that isn't uploaded, like the chatbot's `.env`.
- [ ] Both servers were restarted after the changes.
- [ ] `python check.py` (in `Chatbot/`) says all good.
- [ ] The laptop is plugged in, and won't go to sleep (Windows *Settings → System → Power*: set
      "When plugged in, put my device to sleep after" to **Never** while it's hosting).
- [ ] The papers in `papers/README.md` are listed, since the website shows answers from them.
- [ ] A privacy policy says what the forms store (names, emails) and why.

## Good to know

- **`runserver` is Django's test server.** It's fine for showing the site for a while from your
  laptop, but Django says not to use it for a real, permanent website (it isn't built for many
  visitors or for security). A real host uses a proper server program instead (e.g. Gunicorn or
  Waitress) and sends the CSS, JavaScript and images with `collectstatic` or WhiteNoise.
  That's also why `runserver` needs `--insecure` to send them when `DEBUG = False`.
- **When your laptop is off**, the website can't be reached at all (it runs on the laptop).
- **When only the chatbot is off**, the website works, and the chat panel says *"The chatbot can't
  be reached right now. Please try again later."*
- **One question at a time:** Ollama answers one question at a time. If two visitors ask at once,
  the second waits until the first answer is finished.
- **The question limit** (10 questions per visitor per minute) still works through the tunnel: the
  server reads each visitor's real address from Cloudflare (`visitor_address` in `api.py`).
- **Privacy:** questions and form data pass through Cloudflare's network. `logs/server.log` stores
  the first 80 characters of a question only when something went wrong with it.
- **The chatbot's `/docs` test page** is public through the tunnel too. It only lets people ask
  questions, which they can also do on the website, so that's not a problem.
