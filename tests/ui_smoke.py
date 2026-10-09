"""Responsive layout and settings modal checks; no provider requests."""
import os
from playwright.sync_api import sync_playwright
from fixtures import seed_bank
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width':1440, 'height':1000})
    seed_bank(page)
    page.goto(os.environ.get('TEST_URL', 'http://127.0.0.1:8000'))
    page.locator('[data-action="explain"]').first.click()
    assert page.locator('.question-card').first.bounding_box()['x'] + page.locator('.question-card').first.bounding_box()['width'] <= page.locator('#ai-dialog').bounding_box()['x']
    assert page.locator('#ai-dialog #ai-provider').count() == 0
    assert page.locator('#ai-welcome').is_visible()
    page.locator('#ai-dialog .ai-settings-open').click()
    assert page.locator('#ai-settings-dialog').evaluate('(e)=>e.matches(":modal")')
    page.keyboard.press('Escape')
    assert not page.locator('#ai-settings-dialog').is_visible()
    assert page.locator('#ai-dialog .ai-settings-open').evaluate('(e)=>e===document.activeElement')
    page.set_viewport_size({'width':390,'height':844})
    page.wait_for_function('parseFloat(document.documentElement.style.getPropertyValue("--visual-height")) <= 844')
    assert page.locator('#ai-send').bounding_box()['y'] + page.locator('#ai-send').bounding_box()['height'] <= 844
    page.locator('#ai-dialog .ai-settings-open').click()
    assert page.locator('#ai-settings-dialog').bounding_box()['width'] <= 390
    page.locator('#ai-key').fill('unsubmitted-test-key')
    page.keyboard.press('Escape')
    page.wait_for_function('document.querySelector("#ai-key").value === ""')
    page.locator('#ai-close').click()
    page.locator('#filters-toggle').click()
    assert page.locator('#search-input').is_visible()
    page.locator('#sidebar-close').click()
    assert not page.locator('#search-input').is_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    print('PASS desktop tutor separation, modal isolation/focus return, mobile composer, key field clearing, filter drawer and overflow')
    browser.close()
