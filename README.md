# UPSC Vault

A responsive question bank with CSV import, answer feedback, bookmarks, notes, image attachments, themes, and a question-aware AI tutor. Practice works without external scripts or an internet connection after loading the page. Progress is saved in the browser.

## Run

Python 3.10+ is the only runtime dependency:

```sh
python3 server.py
```

The default port is 8000; set `PORT` to change it. The server binds to loopback for local development.

## AI explanations

Open the separate **AI settings** popup from the page header or the tutor’s gear button. Choose your provider, choose a model, enter the matching API key and click **Connect key**. This supports DeepSeek paid keys, OpenRouter keys, and OpenAI keys on both static hosting and the local server. Each provider's key is kept separate; switching providers never sends one provider's key to another. Check **Remember on this device** to restore that key and model after refreshing. Without this option, the key stays in memory and clears on refresh.

- **DeepSeek:** `deepseek-chat` for quick explanations, `deepseek-reasoner` for deeper reasoning. Your paid API balance is used.
- **OpenRouter:** the picker fetches `/api/v1/models` and lists only `:free` text models with zero prompt and completion prices. It suggests a reasoning model with longer context using a heuristic, not a UPSC accuracy benchmark. `openrouter/free` is an automatic free-model router available as a fallback. Free models have rate limits and may be removed. No paid model fallback is selected by the picker.
- **OpenAI:** GPT-4o mini and GPT-4.1 variants.

For server-side configuration instead, set `AI_PROVIDER` to `deepseek`, `openrouter`, or `openai` and supply `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`, or `OPENAI_API_KEY` respectively. `AI_API_KEY` is a fallback for the configured provider. Optional `AI_MODEL` overrides its default (`deepseek-chat`, `openrouter/free`, or `gpt-4o-mini`). Restart the server after configuration. Without a connected browser session key, the server uses its own configured provider; the browser picker applies to browser session keys.

Allow `api.deepseek.com`, `openrouter.ai`, or `api.openai.com` as appropriate. TLS verification stays enabled. Keys can be entered securely in cloud environment settings, never in chat or GitHub source.

Use **Explain with AI** to open the right-side tutor without blocking the question page. Ask follow-up questions or choose a suggested prompt. Each question retains its conversation for the current tab session; **New conversation** resets it. Only the selected question, subject, answer key, and the current tutor conversation are sent to the provider. For a configured server, the key stays on the server. Alternatively open the **AI settings** popup, paste the selected provider’s key, and choose **Connect key**. This works on static hosting such as GitHub Pages. Keys are sent directly to the selected provider. Remembered keys are stored in this browser’s localStorage, which is accessible to this website’s scripts and is not an encrypted credential vault; use this option only on a trusted device. Unchecking **Remember on this device** removes the stored key while keeping the current connection until refresh. **Use server** disconnects and removes the selected provider’s saved key. **Forget saved keys** clears all saved and in-memory provider keys. Your keys are not synchronized to GitHub or other devices; clearing browser site data also removes them. Never paste a key into chat or commit it to GitHub. Missing credentials, failed requests, cancellation, and provider limits produce visible messages. Replies render headings, emphasis, lists, quotes, code, and comparison tables using safe DOM nodes; provider-supplied HTML is displayed as inert text. Initial explanations are prompted to stay concise, with more detail available through follow-ups. A live provider call requires credentials and may incur usage charges.

This is a local development server. A public deployment needs authenticated access and rate limiting on the AI route before exposure.

## CSV

Use `Question,Subject,Year,Official Answer Key` headers. `Question` and `Official Answer Key` are required; Answers accept upper/lowercase `a`–`d`, `(a)`–`(d)`, `A.`, `Option B`, and `1`–`4` (mapped to a–d). Blank, `X`, and unavailable/deleted keys import without grading; no answer is guessed. A single four-digit year is recognized in year labels; unrecognized years import as unknown with a notice. Options in question text use `(a)`–`(d)`. Quoted commas, escaped quotes, and multiline fields are supported. Invalid rows are skipped with an import summary and downloadable row report. If no valid questions remain, the current bank is preserved. Literal `\n` markers in question text are displayed as line breaks. An import replaces the bank and resets filters; old progress remains available if the same bank is imported again.

## Validation

```sh
python3 -m unittest discover -s tests
```

With Playwright and system Chromium installed, start the server and run `python3 tests/browser_smoke.py` and `python3 tests/provider_smoke.py` (`TEST_URL` can override the server address). Browser tests use an isolated browser profile, exercise CSV and persistence, and mock successful AI replies. No live provider call is made. There is no frontend build step.

The redesigned workspace uses a collapsible mobile filter drawer, a right-side tutor with a fixed composer, and a separate modal for provider/model/key configuration. Escape closes settings and returns focus to its opener. The tutor’s current-question reference is collapsible, and suggestion prompts hide when a conversation begins.

Run `python3 tests/formatting_smoke.py` against the development server to check tutor formatting, mobile overflow, retained conversations, and inert HTML handling.

## Focused practice

New browsers start with an import screen; there is no demo loader or automatic sample bank. Existing saved questions and progress are retained. Banks display 20 questions per page; changing filters starts at the first page. Use **Unanswered** to work through new questions or **Review mistakes** to revisit incorrect answers. View results refresh when you change filters; the current question stays visible after answering so you can review its feedback.

An answer locks after selection. **Try again** clears that question's current answer and reveal state while retaining notes and bookmarks. Accuracy reflects current graded answers, while saved practice results remain snapshots. Questions without an answer key stay ungraded.

Use **Save to question notes** below a tutor reply to append it to your existing notes. The text is labeled as an AI explanation and can be edited. **Give me a hint** instructs the model to offer a clue without revealing the answer; actual model compliance may vary.

Run `python3 tests/learning_smoke.py` to check the import-first experience, pagination, revision views, retries, and saved explanations. Browser regression fixtures live only in `tests/fixtures.py`.

Run `python3 tests/remember_smoke.py` for opt-in key/model restoration, session-only behavior, and saved-key removal checks using synthetic credentials.

## Tablets and browser compatibility

The sidebar starts collapsed at tablet widths (up to 1200 CSS pixels, or up to 1366 with a touch pointer), including 11-inch iPad portrait and landscape sizes. Open it with **Filters** and close it with its × button, the backdrop, or Escape. Desktop users can also hide it; the desktop collapsed preference survives refresh. Opening the tutor closes the tablet drawer.

Landscape tablet layouts keep questions beside the tutor. Narrower views use a tutor overlay. Touch targets are at least 44 pixels, touch inputs use 16-pixel text to avoid Safari focus zoom, and the composer follows the visual viewport as the software keyboard changes available space. Dynamic viewport sizing has fallbacks, and safe-area padding protects the bottom controls.

`TEST_BROWSER=webkit python3 tests/tablet_smoke.py` runs the same seven iPad-size checks as Chromium (default). Install the desired engine with `python3 -m playwright install --with-deps webkit`. The Browser compatibility GitHub Actions workflow runs Chromium and WebKit on pushes to main and pull requests. These are engine/device emulation checks, not physical iPad testing.

## Tutor models, notes and panel size

OpenRouter settings default to free text models. Enable **Include paid GPT-4o and DeepSeek models** to show those currently in the live catalog, then explicitly select one. Paid entries show input/output prices per million tokens and require OpenRouter credits. Your direct DeepSeek key continues to work under the DeepSeek provider. Content moderation models are excluded from study suggestions.

Reasoning models receive a larger output allowance (up to 8,000 tokens) and a two-minute browser timeout. Supported OpenRouter models use low reasoning effort. Temporary free-model capacity errors receive one short retry; paid requests are never automatically retried or selected as a fallback. Empty or truncated answers leave your question available to retry. Provider availability and accuracy cannot be guaranteed.

Drag the tutor's left edge to resize it on tablets and desktops. The focused handle supports arrow keys, Home to reset, and End to maximize; width is remembered and constrained to the viewport. Phones keep a full-width panel.

Saved AI notes remove Markdown heading, emphasis and table syntax while preserving readable text. Use **Clean formatting** on existing notes, with **Undo cleanup** available until refresh. Run `python3 tests/tutor_reliability_smoke.py` for mocked recovery, paid model filtering, note cleanup and resizing checks; it also supports `TEST_BROWSER=webkit`.

Follow-up questions send the complete successful conversation for the current exam question, including previous assistant answers. Closing and reopening the tutor or visiting another question retains that question’s chat until the page is refreshed. **New conversation** explicitly resets it. The app stops with a clear message at 99 messages or a 240 KB request rather than silently dropping older turns. Provider context limits may be lower. Follow-up instructions resolve references against the preceding answer; model understanding still varies. Run `python3 tests/followup_smoke.py` to verify the history sent through direct and server connections.
