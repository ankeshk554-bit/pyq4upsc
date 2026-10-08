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

Use **Explain with AI** to open the right-side tutor without blocking the question page. Ask follow-up questions or choose a suggested prompt. Each question retains its conversation for the current tab session; **New conversation** resets it. Only the selected question, subject, answer key, and the current tutor conversation are sent to the provider. For a configured server, the key stays on the server. Alternatively open **AI connection settings** in the tutor, paste your own OpenAI key, and choose **Connect key**. This works on static hosting such as GitHub Pages. The session key is held only in memory, sent directly to OpenAI, and cleared on refresh; **Use server** clears it immediately. Never paste a key into chat or commit it to GitHub. Missing credentials, failed requests, cancellation, and provider limits produce visible messages. Generated replies are rendered as text. A live provider call requires credentials and may incur usage charges.

This is a local development server. A public deployment needs authenticated access and rate limiting on the AI route before exposure.

## CSV

Use `Question,Subject,Year,Official Answer Key` headers. `Question` and `Official Answer Key` are required; Answers accept upper/lowercase `a`–`d`, `(a)`–`(d)`, `A.`, `Option B`, and `1`–`4` (mapped to a–d). Blank, `X`, and unavailable/deleted keys import without grading; no answer is guessed. A single four-digit year is recognized in year labels; unrecognized years import as unknown with a notice. Options in question text use `(a)`–`(d)`. Quoted commas, escaped quotes, and multiline fields are supported. Invalid rows are skipped with an import summary and downloadable row report. If no valid questions remain, the current bank is preserved. Literal `\n` markers in question text are displayed as line breaks. An import replaces the bank and resets filters; old progress remains available if the same bank is imported again.

## Validation

```sh
python3 -m unittest discover -s tests
```

With Playwright and system Chromium installed, start the server and run `python3 tests/browser_smoke.py` (`TEST_URL` can override the server address). Browser tests use an isolated browser profile, exercise CSV and persistence, and mock successful AI replies. No live provider call is made. There is no frontend build step.
