"""Opt-in browser connection persistence and deletion; synthetic keys only."""
import os
from playwright.sync_api import sync_playwright
from fixtures import seed_bank
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page();seed_bank(page)
    page.goto(os.environ.get('TEST_URL','http://127.0.0.1:8000'))
    def settings():
        page.locator('.topbar .ai-settings-open').click()
    settings()
    page.locator('#ai-provider').select_option('deepseek')
    page.locator('#ai-model').select_option('deepseek-reasoner')
    page.locator('#ai-key').fill('synthetic-deepseek-key')
    page.locator('#ai-remember').check()
    page.locator('#ai-settings-form button[type="submit"]').click()
    assert 'remembered on this device' in page.locator('#ai-connection-status').inner_text()
    page.reload();settings()
    assert page.locator('#ai-provider').input_value()=='deepseek'
    assert page.locator('#ai-model').input_value()=='deepseek-reasoner'
    assert page.locator('#ai-remember').is_checked()
    assert page.locator('#ai-key').input_value()==''
    requests=[]
    page.route('https://api.deepseek.com/chat/completions',lambda route:(requests.append(route.request),route.fulfill(json={'choices':[{'message':{'content':'Remembered connection works.'}}]})))
    page.locator('#ai-settings-done').click();page.locator('[data-action="explain"]').first.click();page.locator('#ai-send').click()
    page.locator('.ai-message.assistant').wait_for()
    assert requests[-1].headers['authorization']=='Bearer synthetic-deepseek-key'
    assert requests[-1].post_data_json['model']=='deepseek-reasoner'
    page.locator('#ai-close').click();settings()
    page.locator('#ai-remember').uncheck()
    assert page.evaluate('localStorage.getItem("uv_ai_connection_v1_deepseek")') is None
    page.reload();settings()
    assert 'No browser key connected' in page.locator('#ai-connection-status').inner_text()
    page.locator('#ai-key').fill('synthetic-session-key');page.locator('#ai-settings-form button[type="submit"]').click()
    page.reload();settings()
    assert 'No browser key connected' in page.locator('#ai-connection-status').inner_text()
    for provider in ['deepseek','openai']:
        page.locator('#ai-provider').select_option(provider)
        page.locator('#ai-key').fill('synthetic-'+provider+'-key');page.locator('#ai-remember').check()
        page.locator('#ai-settings-form button[type="submit"]').click()
    page.locator('#ai-forget-all').click()
    page.reload();settings()
    for provider in ['openai','deepseek']:
        page.locator('#ai-provider').select_option(provider)
        assert not page.locator('#ai-remember').is_checked()
        assert 'No browser key connected' in page.locator('#ai-connection-status').inner_text()
    # Corrupt records must not break initialization.
    page.evaluate('localStorage.setItem("uv_ai_connection_v1_deepseek", "invalid JSON")')
    page.reload();assert page.locator('.question-card').count()==10
    print('PASS remembered key/model/provider restore, request authentication after reload, opt-out, session-only refresh, forget-all and malformed storage')
    browser.close()
