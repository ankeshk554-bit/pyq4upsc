"""Reading-room layout, filter removal, note controls and retained appearance preferences."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from fixtures import seed_bank
URL = os.environ.get('TEST_URL', 'http://127.0.0.1:8000')
with sync_playwright() as p:
    name = os.environ.get('TEST_BROWSER', 'chromium')
    launch_options = {'executable_path':'/usr/bin/chromium', 'args':['--no-sandbox']} if name == 'chromium' and Path('/usr/bin/chromium').exists() else {}
    browser = getattr(p, name).launch(**launch_options)
    page = browser.new_page(viewport={'width':1440,'height':1000})
    seed_bank(page)
    errors=[]
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(URL)
    expect(page.locator('html')).to_have_attribute('data-theme','paper')
    assert 'Georgia' in page.locator('.question-stem').first.evaluate('(e)=>getComputedStyle(e).fontFamily')
    page.locator('[data-year="2024"]').click()
    page.locator('[data-subject="Polity"]').click()
    expect(page.locator('.question-card')).to_have_count(1)
    expect(page.locator('[data-subject="Polity"]')).to_have_attribute('aria-pressed','true')
    page.get_by_role('button',name='Remove filter: 2024',exact=True).click()
    expect(page.locator('.question-card')).to_have_count(2)
    page.locator('#search-input').fill('<script>not code</script>')
    expect(page.locator('.filter-token')).to_have_count(2)
    assert page.locator('#active-filters script').count()==0
    page.get_by_role('button',name='Remove filter: Search: <script>not code</script>',exact=True).click()
    page.get_by_role('button',name='Remove filter: Polity',exact=True).click()
    expect(page.locator('.question-card')).to_have_count(10)
    expect(page.locator('#study-view')).to_be_focused()
    note=page.locator('[data-action="toggle-note"]').first
    note.click();expect(note).to_have_attribute('aria-expanded','true')
    expect(page.locator('[data-note-id]').first).to_be_focused()
    page.locator('[data-note-id]').first.fill('A useful revision note.')
    note.click();expect(note).to_have_attribute('aria-expanded','false')
    expect(page.locator('.notes').first).to_be_hidden()
    page.locator('#notes-open').click()
    expect(page.locator('#notes-reader')).to_contain_text('A useful revision note.')
    page.locator('[data-close="notes-dialog"]').click()
    # Existing user choices must survive the new defaults and a reload.
    page.locator('.topbar .ai-settings-open').click()
    page.locator('#appearance-theme').select_option('nord')
    page.locator('#text-style').select_option('sans')
    page.locator('#text-size').select_option('1.3')
    page.reload()
    expect(page.locator('html')).to_have_attribute('data-theme','nord')
    assert 'sans-serif' in page.locator('.question-stem').first.evaluate('(e)=>getComputedStyle(e).fontFamily')
    for width in [320,390,834,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
        page.locator('[data-action="explain"]').first.click()
        assert page.locator('#ai-dialog').evaluate('(e)=>e.scrollWidth <= e.clientWidth'),width
        page.locator('#ai-close').click()
    assert not errors,errors
    browser.close()
    print('PASS reading defaults, filter removal and escaping, note toggles/focus, notes library, retained appearance and large-text layouts')
