"""Check readable tutor formatting and inert model-supplied HTML."""
import os
from playwright.sync_api import sync_playwright
from fixtures import seed_bank
REPLY = '''# Alternative Investment Funds (AIFs) — Analysis

## What are AIFs?

In India, **Alternative Investment Funds** are *privately pooled* investment vehicles.

| Category | Nature | Examples |
|----------|--------|----------|
| **Category I** | Development | Venture Capital Funds |
| **Category III** | Complex strategies | Hedge Funds |

## Count

- **Hedge Funds (II)**
- **Venture Capital (IV)**

**Answer: (b) Only two**

> **AIF = a privately pooled fund vehicle**, not an individual security.

1. Remember the three categories.
2. Distinguish instruments from funds.

<script>window.aiInjected = true</script>
<img src=x onerror="window.aiInjected=true">

`<svg onload=window.aiInjected=true>`
'''
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':390, 'height':844})
    page.route('**/api/explain', lambda route: route.fulfill(json={'reply':REPLY}))
    seed_bank(page)
    page.goto(os.environ.get('TEST_URL', 'http://127.0.0.1:8000'))
    page.locator('[data-action="explain"]').first.click()
    page.locator('#ai-send').click()
    answer = page.locator('.ai-message.assistant')
    answer.wait_for()
    assert answer.locator('h3').inner_text() == 'Alternative Investment Funds (AIFs) — Analysis'
    assert answer.locator('h4').count() == 2
    assert answer.locator('table tbody tr').count() == 2
    assert answer.locator('table th').count() == 3
    assert answer.locator('strong').count() >= 5
    assert answer.locator('em').inner_text() == 'privately pooled'
    assert answer.locator('ul li').count() == 2
    assert answer.locator('ol li').count() == 2
    assert answer.locator('blockquote').count() == 1
    assert '**' not in answer.inner_text() and '|---' not in answer.inner_text()
    assert answer.locator('script,img,svg').count() == 0
    assert not page.evaluate('Boolean(window.aiInjected)')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.locator('#ai-close').click()
    page.locator('[data-action="explain"]').first.click()
    assert page.locator('.ai-message.assistant table').count() == 1
    page.screenshot(path='/tmp/tutor-formatted.png')
    print('PASS headings, emphasis, tables, lists, quotes, mobile layout, retained formatting and inert HTML')
    browser.close()
