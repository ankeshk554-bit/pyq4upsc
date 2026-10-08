# UPSC Vault

A responsive question bank with CSV import, answer feedback, bookmarks, notes, image attachments, themes, and a question-aware AI tutor. Practice works without external scripts or an internet connection after loading the page. Progress is saved in the browser.

## Run

Python 3.10+ is the only runtime dependency:

```sh
python3 server.py
```

The default port is 8000; set `PORT` to change it. The server binds to loopback for local development.

## AI explanations

Set `AI_API_KEY` securely in the server environment (or use an existing `OPENAI_API_KEY`). Optionally set `AI_MODEL`; the default is `gpt-4o-mini`. Restart the server after configuration. The server calls `https://api.openai.com/v1/chat/completions` with TLS verification. Allow `api.openai.com` in restricted environments.

Use **Explain with AI** on a question, then ask follow-up questions. Only the selected question, subject, answer key, and the current tutor conversation are sent to the provider. Keys are never entered into or stored by the browser. Missing credentials, failed requests, cancellation, and provider limits produce visible messages. Generated replies are rendered as text. A live provider call requires credentials and may incur usage charges.

This is a local development server. A public deployment needs authenticated access and rate limiting on the AI route before exposure.

## CSV

Use `Question,Subject,Year,Official Answer Key` headers. `Question` and `Official Answer Key` are required; answers must be `a`–`d` or `(a)`–`(d)`. Years, when present, must contain four digits. Options in question text use `(a)`–`(d)`. Quoted commas, escaped quotes, and multiline fields are supported. Invalid imports preserve the current bank. An import replaces the bank and resets filters; old progress remains available if the same bank is imported again.

## Validation

```sh
python3 -m unittest discover -s tests
```

With Playwright and system Chromium installed, start the server and run `python3 tests/browser_smoke.py` (`TEST_URL` can override the server address). Browser tests use an isolated browser profile, exercise CSV and persistence, and mock successful AI replies. No live provider call is made. There is no frontend build step.
