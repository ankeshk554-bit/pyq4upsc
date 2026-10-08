"""Provider and free-model picker checks with mock API responses; no live billing."""
import os
from playwright.sync_api import sync_playwright
from fixtures import seed_bank

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page()
    seed_bank(page)
    page.goto(os.environ.get('TEST_URL', 'http://127.0.0.1:8000'))
    page.locator('[data-action="explain"]').first.click()
    def open_settings():
        if not page.locator('#ai-settings-dialog').is_visible():
            page.locator('#ai-dialog .ai-settings-open').click()
    open_settings()
    open_settings()
    page.locator('#ai-provider').select_option('deepseek')
    assert page.locator('#ai-model option').all_text_contents() == ['DeepSeek Chat · fast explanations', 'DeepSeek Reasoner · deeper reasoning']
    page.locator('#ai-key').fill('deepseek-test-key')
    page.locator('#ai-settings-form button[type="submit"]').click()
    page.locator('#ai-settings-done').click()
    requests = []
    def reply(route):
        requests.append((route.request.url, route.request.headers, route.request.post_data_json))
        route.fulfill(json={'choices':[{'message':{'content':'Explanation from selected provider.'}}]})
    page.route('https://api.deepseek.com/chat/completions', reply)
    page.locator('#ai-send').click()
    page.wait_for_function('document.querySelectorAll(".ai-message.assistant").length===1')
    assert requests[-1][1]['authorization']=='Bearer deepseek-test-key'
    assert requests[-1][2]['model']=='deepseek-chat'
    catalog = {'data':[
        {'id':'study/reasoning:free','name':'Study Reasoning','context_length':128000,'pricing':{'prompt':'0','completion':'0'},'architecture':{'output_modalities':['text']}},
        {'id':'study/small:free','name':'Small','context_length':8000,'pricing':{'prompt':'0','completion':'0'}},
        {'id':'study/paid','name':'Paid','pricing':{'prompt':'0.001','completion':'0.002'}},
        {'id':'study/not-free:free','name':'Mislabeled paid','pricing':{'prompt':'0.001','completion':'0'}},
        {'id':'image/image:free','name':'Image','pricing':{'prompt':'0','completion':'0'},'architecture':{'output_modalities':['image']}},
    ]}
    page.route('https://openrouter.ai/api/v1/models',lambda route:route.fulfill(json=catalog))
    open_settings()
    page.locator('#ai-provider').select_option('openrouter')
    page.wait_for_function('document.querySelectorAll("#ai-model option").length===3')
    assert page.locator('#ai-model').input_value()=='study/reasoning:free'
    assert 'Suggested for study' in page.locator('#ai-model option').nth(1).inner_text()
    assert 'No browser key' in page.locator('#ai-connection-status').inner_text()
    assert page.locator('#ai-key').input_value()==''
    page.locator('#ai-key').fill('openrouter-test-key')
    page.locator('#ai-settings-form button[type="submit"]').click()
    page.locator('#ai-settings-done').click()
    page.route('https://openrouter.ai/api/v1/chat/completions',reply)
    page.locator('#ai-question').fill('What is the revision takeaway?')
    page.locator('#ai-send').click()
    page.wait_for_function('document.querySelectorAll(".ai-message.assistant").length===2')
    assert requests[-1][1]['authorization']=='Bearer openrouter-test-key'
    assert requests[-1][2]['model']=='study/reasoning:free'
    assert len(requests[-1][2]['messages'])==4
    open_settings()
    page.locator('#ai-provider').select_option('deepseek')
    assert 'DeepSeek session key' in page.locator('#ai-connection-status').inner_text()
    page.locator('#ai-settings-done').click()
    page.locator('#ai-question').fill('Give another example')
    page.locator('#ai-send').click()
    page.wait_for_function('document.querySelectorAll(".ai-message.assistant").length===3')
    assert requests[-1][1]['authorization']=='Bearer deepseek-test-key'
    assert 'test-key' not in page.evaluate('JSON.stringify(localStorage)+JSON.stringify(sessionStorage)')
    page.unroute('https://openrouter.ai/api/v1/models')
    page.route('https://openrouter.ai/api/v1/models',lambda route:route.fulfill(status=503,json={'error':'Unavailable'}))
    open_settings()
    page.locator('#ai-provider').select_option('openrouter')
    page.wait_for_function('document.querySelector("#ai-model-help").textContent.includes("Could not load")')
    assert page.locator('#ai-model').input_value()=='openrouter/free'
    assert page.locator('#ai-model option').count()==1
    print('PASS DeepSeek routing, provider key isolation, free-model filtering/recommendation, OpenRouter follow-ups and catalog failure fallback')
    browser.close()
