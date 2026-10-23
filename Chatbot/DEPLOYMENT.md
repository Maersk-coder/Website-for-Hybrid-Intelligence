# Putting the chatbot online

Two things have to go online:

1. **The website** (the HTML, CSS and JavaScript in `Front Pages/`, plus the chat panel in
   `Chatbot/widget/`). These are just files, which is easy and free.
2. **The chatbot server** (`api.py` + Ollama + the search index). This is the hard part, because the
   AI model needs a lot of memory and works best with a graphics card.

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

The rest of this file explains **route A**, step by step.

---

## Route A, step by step

### Step 1: The website on GitHub Pages (once)

GitHub can publish the files in your repository as a website, for free.

1. Go to your repository on github.com: **Maersk-coder/Website-for-Hybrid-Intelligence**.
2. Click **Settings** (top), then **Pages** (left).
3. Under *Build and deployment*: Source = **Deploy from a branch**, Branch = **main**, folder = **/ (root)**.
   Click **Save**.
4. Wait 1–2 minutes. The site is then online at:
   `https://maersk-coder.github.io/Website-for-Hybrid-Intelligence/Front%20Pages/Front_Page.html`
   (`%20` is how a space in a folder name is written in a web address.)

From now on, every `git push` updates the website within a minute or two.

The chat panel works on this page as soon as steps 2–4 are done. Until then it says it can't
reach the chatbot.

### Step 2: Install Cloudflare's tunnel program (once)

In a terminal:

```powershell
winget install --id Cloudflare.cloudflared
```

Close the terminal and open a new one, so Windows finds the new program.

### Step 3: Start everything

Three things must run at the same time, each in its own terminal (Ollama runs by itself):

1. **Ollama:** check for the llama icon near the clock.
2. **The chatbot server**, in the Chatbot folder with `(.venv)` on:
   ```powershell
   python api.py
   ```
3. **The tunnel**, in a new terminal:
   ```powershell
   cloudflared tunnel --url http://127.0.0.1:8000
   ```
   After a few seconds it prints an address like `https://some-random-words.trycloudflare.com`.
   That is your chatbot's public address. Copy it.

Check it: open `https://some-random-words.trycloudflare.com/health` in your browser. You should see `"status":"ok"`.

### Step 4: Tell the website and the server about each other

**The website must know the chatbot's address.** In `Front Pages/Front_Page.html`, near the bottom,
change `data-api` to the tunnel's address (no `/` at the end):

```html
<script src="../Chatbot/widget/chat-widget.js" data-api="https://some-random-words.trycloudflare.com" data-target="#hi-chat"></script>
```

**The server must allow the website.** In `Chatbot/.env`, set `ALLOWED_ORIGINS` to the GitHub Pages
address (only the start, without the path), and **remove `,null`**:

```
ALLOWED_ORIGINS=https://maersk-coder.github.io
```

Keep the Live Server addresses in the list too if you still want to test locally:
`ALLOWED_ORIGINS=https://maersk-coder.github.io,http://127.0.0.1:5500,http://localhost:5500`

Then:
- restart `api.py` (Ctrl+C, then `python api.py`), because `.env` is only read at the start;
- commit and push `Front_Page.html`, so GitHub Pages gets the new address.

Open the GitHub Pages address, scroll to Page 3 and ask a question.

### Important: the tunnel address changes

The free "quick tunnel" gets a **new random address every time** you start `cloudflared`. Each
time, step 4 (`data-api` + push) must be done again. Cloudflare also says quick tunnels are meant
for testing, not for a permanent website.

For a **permanent address**: create a free Cloudflare account, buy a domain name (about €10 a year,
e.g. `hybrid-intelligence-chat.com`) and set up a *named tunnel* for it
([Cloudflare's guide](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/)).
The address then stays the same, and step 4 is done only once.

---

## Checklist before going online

- [ ] `,null` is removed from `ALLOWED_ORIGINS` in `.env` (it was only for testing on your own computer).
- [ ] `ALLOWED_ORIGINS` contains `https://maersk-coder.github.io`.
- [ ] `data-api` in `Front_Page.html` is the tunnel's address, and the change is pushed to GitHub.
- [ ] `api.py` was restarted after changing `.env`.
- [ ] `python check.py` says all good.
- [ ] The laptop is plugged in, and won't go to sleep (Windows *Settings → System → Power*: set
      "When plugged in, put my device to sleep after" to **Never** while it's hosting).
- [ ] The papers in `papers/README.md` are listed, since the website now shows answers from them.

## Good to know

- **When your laptop is off**, the chat panel says *"The chatbot can't be reached right now. Please
  try again later."* The rest of the website keeps working.
- **One question at a time:** Ollama answers one question at a time. If two visitors ask at once,
  the second waits until the first answer is finished.
- **The question limit** (10 questions per visitor per minute) still works through the tunnel: the
  server reads each visitor's real address from Cloudflare (`visitor_address` in `api.py`).
- **Privacy:** questions pass through Cloudflare's network. `logs/server.log` stores the first 80
  characters of a question only when something went wrong with it. Mention this in your privacy
  policy if you have one.
- **The `/docs` test page** is public through the tunnel too. It only lets people ask questions,
  which they can also do on the website, so that's not a problem.
