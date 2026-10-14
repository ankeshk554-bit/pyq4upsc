# UPSC Vault

A responsive question bank with an automatically loaded question bank, answer feedback, bookmarks, notes, image attachments, themes, and a question-aware AI tutor. Practice works without external scripts or an internet connection after loading the page. Progress is saved in the browser.

## Run

Python 3.10+ is the only runtime dependency:

```sh
python3 server.py
```

The default port is 8000; set `PORT` to change it. The server binds to loopback for local development.

## AI explanations

Open **Settings** from the top bar or the tutor’s gear button, then select the **AI** tab. Choose your provider, choose a model, enter the matching API key and click **Connect key**. This supports DeepSeek paid keys, OpenRouter keys, and OpenAI keys on both static hosting and the local server. Each provider's key is kept separate; switching providers never sends one provider's key to another. Check **Remember on this device** to restore that key and model after refreshing. Without this option, the key stays in memory and clears on refresh.

- **DeepSeek:** `deepseek-chat` for quick explanations, `deepseek-reasoner` for deeper reasoning. Your paid API balance is used.
- **OpenRouter:** the picker fetches `/api/v1/models` and defaults to `:free` text models with zero prompt and completion prices. It suggests a reasoning model with longer context using a heuristic, not a UPSC accuracy benchmark. `openrouter/free` is an automatic free-model router available as a fallback. Free models have rate limits and may be removed. No paid model fallback is selected by the picker.
- **OpenAI:** GPT-4o, GPT-4o mini and GPT-4.1 variants.

For server-side configuration instead, set `AI_PROVIDER` to `deepseek`, `openrouter`, or `openai` and supply `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`, or `OPENAI_API_KEY` respectively. `AI_API_KEY` is a fallback for the configured provider. Optional `AI_MODEL` overrides its default (`deepseek-chat`, `openrouter/free`, or `gpt-4o-mini`). Restart the server after configuration. Without a connected browser session key, the server uses its own configured provider; the browser picker applies to browser session keys.

Allow `api.deepseek.com`, `openrouter.ai`, or `api.openai.com` as appropriate. TLS verification stays enabled. Keys can be entered securely in cloud environment settings, never in chat or GitHub source.

Use **Explain with AI** to open the right-side tutor without blocking the question page. Ask follow-up questions or choose a suggested prompt. Each question retains its conversation for the current tab session; **New conversation** resets it. Only the selected question, subject, answer key, and the current tutor conversation are sent to the provider. For a configured server, the key stays on the server. Alternatively open **Settings → AI**, paste the selected provider’s key, and choose **Connect key**. This works on static hosting such as GitHub Pages. Keys are sent directly to the selected provider. Remembered keys are stored in this browser’s localStorage, which is accessible to this website’s scripts and is not an encrypted credential vault; use this option only on a trusted device. Unchecking **Remember on this device** removes the stored key while keeping the current connection until refresh. **Use server** disconnects and removes the selected provider’s saved key. **Forget saved keys** clears all saved and in-memory provider keys. Your keys are not synchronized to GitHub or other devices; clearing browser site data also removes them. Never paste a key into chat or commit it to GitHub. Missing credentials, failed requests, cancellation, and provider limits produce visible messages. Replies render headings, emphasis, lists, quotes, code, and comparison tables using safe DOM nodes; provider-supplied HTML is displayed as inert text. Initial explanations are prompted to stay concise, with more detail available through follow-ups. A live provider call requires credentials and may incur usage charges.

This is a local development server. A public deployment needs authenticated access and rate limiting on the AI route before exposure.

## CSV

Use `Question,Subject,Year,Official Answer Key` headers. `Question` and `Official Answer Key` are required; Answers accept upper/lowercase `a`–`d`, `(a)`–`(d)`, `A.`, `Option B`, and `1`–`4` (mapped to a–d). Blank, `X`, and unavailable/deleted keys import without grading; no answer is guessed. A single four-digit year is recognized in year labels; unrecognized years import as unknown with a notice. Options in question text use `(a)`–`(d)`. Quoted commas, escaped quotes, and multiline fields are supported. Invalid rows are skipped by the shared CSV parser. If no valid questions remain, the current bank is preserved. Literal `\n` markers in question text are displayed as line breaks. Published updates replace the cached bank; progress remains linked to unchanged question IDs.

## Validation

```sh
python3 -m unittest discover -s tests
```

With Playwright and system Chromium installed, start the server and run `python3 tests/browser_smoke.py` and `python3 tests/provider_smoke.py` (`TEST_URL` can override the server address). Browser tests use an isolated browser profile, exercise CSV and persistence, and mock successful AI replies. No live provider call is made. There is no frontend build step.

The redesigned workspace uses a collapsible mobile filter drawer, a right-side tutor with a fixed composer, and a unified Settings panel for appearance, reading preferences, provider/model/key configuration, and backups. Escape closes settings and returns focus to its opener. The tutor’s current-question reference is collapsible, and suggestion prompts hide when a conversation begins.

Run `python3 tests/formatting_smoke.py` against the development server to check tutor formatting, mobile overflow, retained conversations, and inert HTML handling.

## Focused practice

New browsers load the published question bank automatically. Existing browsers show their cached bank while checking for an updated published CSV. Saved answers and notes for unchanged question IDs are retained. Banks display 20 questions per page; changing filters starts at the first page. Use **Unanswered** to work through new questions or **Review mistakes** to revisit incorrect answers. View results refresh when you change filters; the current question stays visible after answering so you can review its feedback.

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

## Publishing and question storage

The site loads `data/questions.csv` automatically on every visit and caches it for future visits. Update that file in the repository to publish revised questions; visitors do not manage CSV files. There are no import or bank-management controls. Saved answers, bookmarks and notes remain linked to unchanged question IDs. Private browsing, clearing site data, changing domains and switching devices do not share local progress.

For an initial public release, static hosting such as GitHub Pages can serve these files. Each user connects their own AI key. Do not put your paid key in frontend code or the published CSV. The Python server is a development tool, not a public AI backend. If you want to provide AI using your own account, add an authenticated backend, per-user quotas/rate limits and spending controls first.

Accounts plus a database are the next step for automatic progress/notes synchronization across devices. Backup and restore provide manual transfer now; automatic account-based synchronization is not configured. Chat history remains limited to the current page session.

## Practice timer

The compact practice header includes an optional session timer. Start it when ready; it counts distinct questions answered while running and shows elapsed minutes/seconds and average time per question. Retrying the same question does not increase the count. Pause excludes breaks; switching away from the tab pauses automatically. Refresh restores the session paused in the same tab. Reset clears only timing and its question count, never study progress. When you scroll past the main timer, a compact bar stays below the navigation with elapsed time, answered count, average pace, and Start/Pause/Resume. Both displays share the same session. **Top** returns to the main timer and its reset control. Question-page navigation leaves the next question below the fixed controls. The timer is a practice aid, not an exam enforcement clock. `tests/timer_smoke.py` checks these controls, scroll visibility at phone/tablet/desktop widths, tutor resizing, pagination clearance, and focus restoration, and supports Chromium/WebKit.

## Notes library and portable study backups

Answers, bookmarks and notes save automatically in one versioned local snapshot. The clickable save status in the header confirms saving or warns of storage failure, and opens Backup & restore. Existing local records migrate after a successful snapshot write. A conflicting write from another tab is blocked: back up that tab and reload before continuing. This protects against silent replacement; it is not collaborative editing. **Save score snapshot** records a result separately from automatic progress saving.

Open **Settings → Data → Backup & restore → Download study backup** to download a JSON file with question metadata, answers, notes, image attachments and score history. API keys, AI conversations and timer state are excluded. Transfer the file to another device, select it in **Backup & restore**, review its counts, then choose **Merge backup**. The merge preserves local-only work, chooses newer answer records (local on a tie), combines differing notes, and retains bookmarks from either copy. Backup writes are committed as one storage operation; an invalid file or storage failure leaves the active data unchanged. Validation limits files to 25 MB; browser storage quotas may be smaller. Device clocks influence newer-record selection. This is manual backup transfer, not continuous cloud sync.

**Notes library** provides subject and text filters, adjustable reading sizes and editing. It retains notes for archived questions after bank updates. **Print / Save PDF** opens your device's print flow for the filtered notes, grouped by subject, with question attachments. Choose Save as PDF where supported. **Download Word** creates a `.docx` containing the same filtered question and note text. Word exports reference image attachments; use PDF or the study backup to include those images. No third-party conversion service receives notes. Browser printing and Microsoft Word rendering can vary; exports are tested structurally and against browser print styles.

Run `python3 tests/study_tools_smoke.py` against the server to test backup round-trips, merge preservation, edits, exports, validation and failed storage. It also runs on WebKit in CI.

## Workspace appearance

The reading-room design uses warm paper surfaces, a deep green filter rail, and serif question text by default. Existing theme and font choices are retained. All styling lives in `styles.css`; deploy it beside `index.html` and `study-tools.js`. The interface uses local system fonts and inline icons with no remote asset dependencies.

**Notes library** is available directly in the top bar. **Settings** gathers **Appearance**, **AI**, and **Data** tabs in one panel. Use Left/Right arrows or Home/End to navigate the tabs; the close button and Done remain visible while a section scrolls. Choose a theme, text size, modern sans/serif/monospace style, and line spacing; the reading preview updates immediately. Reading preferences apply to questions, answer options, tutor replies, and notes and persist on this device. Notes also have a separate base text size under Settings → Appearance. **Reset appearance** restores the default reading preferences without changing study progress or AI keys.

Run `python3 tests/settings_smoke.py` against the development server to check the unified panel, saved preferences, text scaling, reset, keyboard focus, backups, notes navigation, and responsive layouts.

The mobile practice header keeps the timer and statistics compact to bring questions into view sooner. The tutor offers **Connect AI** when neither a browser key nor server configuration is available. The local server's `/api/status` endpoint reports only whether AI is configured; it never returns keys or makes a provider request. Configuration does not verify key validity or provider availability. If the status check fails, the UI reports an unverified connection.

Run `python3 tests/launch_smoke.py` to check the mobile question position, keyboard tabs, visible dialog controls, direct backup access and focus restoration, plus configured, disconnected, static-hosting, and unavailable AI states.

Active year, subject, search, and bookmark/note filters appear above the questions and can be removed individually. Question notes have labeled editors and an explicit open/closed state. Run `python3 tests/design_smoke.py` to check filter removal, safe search labels, note controls, preserved appearance preferences, and large-text layouts.
