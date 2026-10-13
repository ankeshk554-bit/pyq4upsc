"""Launch refinements: compact practice, accessible tabs, honest AI status and backup access."""
import os
from playwright.sync_api import sync_playwright, expect

URL = os.environ.get('TEST_URL', 'http://127.0.0.1:8000')
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':390, 'height':844}, is_mobile=True, has_touch=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.route('**/api/status', lambda route: route.fulfill(json={'configured':False}))
    page.goto(URL)
    expect(page.locator('.question-card').first).to_be_visible()
    first_question = page.locator('.question-card').first.bounding_box()['y']
    assert first_question < 550, first_question
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path='/tmp/launch-refined-mobile.png')

    page.locator('#backup-status').click()
    expect(page.locator('#backup-dialog')).to_contain_text('do not automatically sync')
    page.keyboard.press('Escape')
    expect(page.locator('#backup-status')).to_be_focused()
    page.locator('.topbar .ai-settings-open').click()
    expect(page.locator('#settings-tab-appearance')).to_be_focused()
    page.keyboard.press('ArrowRight')
    expect(page.locator('#settings-tab-ai')).to_have_attribute('aria-selected','true')
    expect(page.locator('#settings-panel-appearance')).to_be_hidden()
    expect(page.locator('#ai-provider')).to_be_visible()
    # The close control and section navigation stay visible while scrolling form fields.
    page.locator('#ai-forget-all').scroll_into_view_if_needed()
    close = page.locator('#ai-settings-close').bounding_box()
    assert close['y'] >= 0 and close['y'] + close['height'] < 844
    expect(page.locator('#settings-tab-data')).to_be_in_viewport()
    page.locator('#settings-tab-ai').focus()
    page.keyboard.press('End')
    expect(page.locator('#settings-tab-data')).to_be_focused()
    page.locator('#backup-open').click()
    expect(page.locator('#ai-settings-dialog')).to_be_hidden()
    page.keyboard.press('Escape')
    expect(page.locator('.topbar .ai-settings-open')).to_be_focused()

    page.locator('[data-action="explain"]').first.click()
    expect(page.locator('#ai-active-connection')).to_have_text('AI not connected')
    page.locator('#ai-connect').click()
    expect(page.locator('#settings-tab-ai')).to_have_attribute('aria-selected','true')
    page.locator('#ai-provider').select_option('deepseek')
    page.locator('#ai-key').fill('synthetic-launch-key')
    page.locator('#ai-settings-form button[type="submit"]').click()
    page.locator('#ai-settings-done').click()
    expect(page.locator('#ai-connect')).to_be_hidden()
    expect(page.locator('#ai-active-connection')).to_contain_text('DeepSeek')

    for status, expected in [('configured','Server AI configured'), ('static','AI not connected'), ('offline','AI connection unverified')]:
        page.unroute('**/api/status')
        if status == 'static':
            page.route('**/api/status', lambda route: route.fulfill(status=404, body='Not found'))
        elif status == 'offline':
            page.route('**/api/status', lambda route: route.abort())
        else:
            page.route('**/api/status', lambda route: route.fulfill(json={'configured':True}))
        page.reload()
        page.locator('[data-action="explain"]').first.click()
        expect(page.locator('#ai-active-connection')).to_have_text(expected)
        if status == 'configured': expect(page.locator('#ai-connect')).to_be_hidden()
        else: expect(page.locator('#ai-connect')).to_be_visible()
        if status == 'static':
            page.route('**/api/explain', lambda route: route.fulfill(status=404, body='Not found'))
            page.locator('#ai-send').click()
            expect(page.locator('.ai-message.error')).to_contain_text('Open Settings → AI')
            page.unroute('**/api/explain')

    page.locator('#ai-close').click()
    for width in [320,390,768,1440]:
        page.set_viewport_size({'width':width,'height':844})
        page.locator('.topbar .ai-settings-open').click()
        for section in ['appearance','ai','data']:
            page.locator('#settings-tab-'+section).click()
            assert page.locator('.settings-content').evaluate('(e)=>e.scrollWidth<=e.clientWidth'), (width,section)
            expect(page.locator('#ai-settings-close')).to_be_in_viewport()
            expect(page.locator('#ai-settings-done')).to_be_in_viewport()
        page.keyboard.press('Escape')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
    page.evaluate('window.scrollTo(0,0)')
    page.screenshot(path='/tmp/launch-refined-desktop.png')
    page.set_viewport_size({'width':390,'height':844})
    page.locator('.topbar .ai-settings-open').click()
    page.screenshot(path='/tmp/launch-refined-settings.png')
    assert not errors, errors
    browser.close()
    print(f'PASS mobile first question at {first_question:.0f}px, keyboard tabs, fixed controls, backup focus, AI configuration states and responsive layouts')
