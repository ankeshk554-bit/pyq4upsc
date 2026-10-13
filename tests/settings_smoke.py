"""Unified settings, persistent reading preferences, and responsive navigation."""
import os
from playwright.sync_api import sync_playwright, expect
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(os.environ.get('TEST_URL', 'http://127.0.0.1:8000'))
    expect(page.locator('.question-card').first).to_be_visible()
    assert page.locator('.topbar #notes-open').count() == 1
    page.locator('.topbar .ai-settings-open').click()
    expect(page.get_by_role('heading', name='Settings', exact=True)).to_be_visible()
    before = page.locator('.question-stem').first.evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)')
    page.locator('#text-size').select_option('1.3')
    page.locator('#text-style').select_option('serif')
    page.locator('#text-spacing').select_option('2.1')
    page.locator('#notes-size').select_option('23')
    page.locator('#appearance-theme').select_option('paper')
    page.locator('#ai-settings-done').click()
    assert page.locator('.question-stem').first.evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)') > before
    page.reload()
    page.locator('.topbar .ai-settings-open').click()
    for control, value in [('text-size','1.3'),('text-style','serif'),('text-spacing','2.1'),('notes-size','23'),('appearance-theme','paper')]:
        expect(page.locator('#'+control)).to_have_value(value)
    page.locator('#settings-tab-data').click()
    page.locator('#backup-open').click()
    expect(page.locator('#backup-dialog')).to_be_visible()
    expect(page.locator('#ai-settings-dialog')).not_to_be_visible()
    page.locator('[data-close="backup-dialog"]').click()
    for width in [390,768,1440]:
        page.set_viewport_size({'width':width,'height':900})
        page.locator('.topbar .ai-settings-open').click()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert page.locator('#ai-settings-dialog').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
        page.locator('#appearance-reset').click()
        expect(page.locator('#text-size')).to_have_value('1')
        page.keyboard.press('Escape')
        expect(page.locator('.topbar .ai-settings-open')).to_be_focused()
        page.locator('#notes-open').click()
        expect(page.locator('#notes-dialog')).to_be_visible()
        page.locator('[data-close="notes-dialog"]').click()
    page.screenshot(path='/tmp/redesigned-workspace.png', full_page=True)
    assert not errors, errors
    browser.close()
    print('PASS unified settings, text scaling, saved preferences, reset, backups, keyboard focus, notes navigation and responsive layouts')
