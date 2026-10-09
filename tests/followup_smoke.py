"""Verify complete conversation context reaches both tutor routes, without live AI calls."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from fixtures import seed_bank

with sync_playwright() as p:
    name = os.environ.get('TEST_BROWSER', 'chromium')
    kwargs = {'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if name == 'chromium' and Path('/usr/bin/chromium').exists() else {}
    browser = getattr(p, name).launch(**kwargs)
    for direct in (False, True):
        page = browser.new_page()
        seed_bank(page)
        requests = []
        def reply(route):
            requests.append(route.request.post_data_json)
            answer = f'Explanation {len(requests)}: hedge funds are pooled investment vehicles.'
            route.fulfill(json={'choices':[{'message':{'content':answer}}]} if direct else {'reply':answer})
        page.route('https://api.deepseek.com/chat/completions' if direct else '**/api/explain', reply)
        page.goto(os.environ.get('TEST_URL','http://127.0.0.1:8000'))
        page.locator('[data-action="explain"]').first.click()
        if direct:
            page.locator('#ai-dialog .ai-settings-open').click()
            page.locator('#ai-provider').select_option('deepseek')
            page.locator('#ai-key').fill('synthetic-test-key')
            page.locator('#ai-settings-form button[type="submit"]').click()
            page.locator('#ai-settings-done').click()
        for turn in range(12):
            prompt = 'Explain hedge funds' if turn == 0 else f'Give an example of that (follow-up {turn})'
            page.locator('#ai-question').fill(prompt)
            page.locator('#ai-send').click()
            page.wait_for_function('(n) => document.querySelectorAll(".ai-message.assistant").length === n',arg=turn+1)
            messages = requests[-1]['messages'][1:] if direct else requests[-1]['messages']
            assert len(messages) == 2*turn+1
            assert messages[0] == {'role':'user','content':'Explain hedge funds'}
            assert messages[-1] == {'role':'user','content':prompt}
            if turn:
                assert messages[-2] == {'role':'assistant','content':f'Explanation {turn}: hedge funds are pooled investment vehicles.'}
            if turn == 1:
                page.locator('#ai-close').click()
                page.locator('[data-action="explain"]').nth(1).click()
                assert page.locator('.ai-message.assistant').count() == 0
                page.locator('#ai-close').click()
                page.locator('[data-action="explain"]').first.click()
        if direct:
            assert 'especially your immediately preceding answer' in requests[-1]['messages'][0]['content']
        page.locator('#ai-new-chat').click()
        page.locator('#ai-question').fill('Start fresh')
        page.locator('#ai-send').click()
        page.wait_for_function('document.querySelectorAll(".ai-message.assistant").length === 1')
        assert len(requests[-1]['messages']) == (2 if direct else 1)
        page.close()
    browser.close()
    print('PASS direct/server full follow-up history beyond nine exchanges, previous answer, per-question isolation, reopening and explicit reset')
