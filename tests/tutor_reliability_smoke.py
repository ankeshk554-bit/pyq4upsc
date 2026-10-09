"""Mocked provider recovery, explicit paid selection, clean notes and resizing."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from fixtures import seed_bank

with sync_playwright() as p:
    name=os.environ.get('TEST_BROWSER','chromium')
    kwargs={'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if name=='chromium' and Path('/usr/bin/chromium').exists() else {}
    browser = getattr(p,name).launch(**kwargs)
    page = browser.new_page(viewport={'width':1194,'height':834})
    seed_bank(page)
    catalog = {'data':[
        {'id':'nvidia/nemotron:free','pricing':{'prompt':'0','completion':'0'},'supported_parameters':['reasoning']},
        {'id':'nvidia/content-safety:free','pricing':{'prompt':'0','completion':'0'}},
        {'id':'openai/gpt-4o','pricing':{'prompt':'0.0000025','completion':'0.00001'}},
        {'id':'deepseek/deepseek-chat','pricing':{'prompt':'0.0000003','completion':'0.000001'}}]}
    page.route('https://openrouter.ai/api/v1/models',lambda r:r.fulfill(json=catalog))
    page.goto(os.environ.get('TEST_URL','http://127.0.0.1:8000'))
    page.locator('[data-action="explain"]').first.click()
    handle=page.locator('#tutor-resize')
    box=handle.bounding_box()
    page.mouse.move(box['x']+8,box['y']+300)
    page.mouse.down(); page.mouse.move(694,box['y']+300); page.mouse.up()
    assert abs(page.locator('#ai-dialog').bounding_box()['width']-500)<2
    handle.focus(); page.keyboard.press('ArrowLeft')
    assert abs(page.locator('#ai-dialog').bounding_box()['width']-524)<2
    page.reload(); page.locator('[data-action="explain"]').first.click()
    assert abs(page.locator('#ai-dialog').bounding_box()['width']-524)<2
    page.locator('#ai-dialog .ai-settings-open').click()
    page.locator('#ai-provider').select_option('openrouter')
    page.wait_for_function('document.querySelectorAll("#ai-model option").length===2')
    page.locator('#ai-include-paid').check()
    page.wait_for_function('document.querySelectorAll("#ai-model option").length===4')
    assert page.locator('#ai-model').input_value()=='nvidia/nemotron:free'
    assert 'PAID' in page.locator('option[value="openai/gpt-4o"]').inner_text()
    page.locator('#ai-key').fill('test-key')
    page.locator('#ai-settings-form button[type="submit"]').click()
    page.locator('#ai-settings-done').click()
    calls=[]
    reply='# AIFs\n\n**Hedge funds** qualify.\n\n| Fund | Category |\n|---|---|\n| VC | I |'
    def respond(route):
        calls.append(route.request.post_data_json)
        if len(calls)==1: route.fulfill(status=503,json={'error':{'code':503}})
        else: route.fulfill(json={'choices':[{'message':{'content':[{'type':'text','text':reply}]}}]})
    page.route('https://openrouter.ai/api/v1/chat/completions',respond)
    page.locator('#ai-send').click()
    page.locator('.ai-message.assistant').wait_for()
    assert len(calls)==2 and calls[-1]['max_tokens']==8000
    assert calls[-1]['reasoning']=={'effort':'low','exclude':True}
    page.locator('.save-ai-note').click()
    page.locator('#ai-close').click()
    note=page.locator('textarea[data-note-id]').first
    saved=note.input_value()
    assert '**' not in saved and '# AIFs' not in saved and '| Fund' not in saved
    assert 'Fund: VC; Category: I' in saved
    note.fill('## Old note\n\n**Important** fact')
    note.blur()
    page.locator('[data-action="clean-note"]').first.click()
    assert note.input_value()=='Old note\n\nImportant fact'
    page.locator('[data-action="undo-note"]').first.click()
    assert '**Important**' in note.input_value()
    page.locator('[data-action="explain"]').first.click()
    page.unroute('https://openrouter.ai/api/v1/chat/completions')
    page.route('https://openrouter.ai/api/v1/chat/completions',lambda r:r.fulfill(json={'choices':[{'message':{'content':None},'finish_reason':'length'}]}))
    page.locator('#ai-question').fill('Explain more')
    page.locator('#ai-send').click()
    page.wait_for_function('document.querySelector(".ai-message.error")?.textContent.includes("output allowance")')
    assert page.locator('#ai-question').input_value()=='Explain more'
    page.locator('#ai-dialog .ai-settings-open').click()
    page.locator('#ai-model').select_option('openai/gpt-4o')
    page.locator('#ai-settings-done').click()
    page.unroute('https://openrouter.ai/api/v1/chat/completions')
    paid_calls=[]
    def paid_error(route):
        paid_calls.append(route.request.post_data_json)
        route.fulfill(json={'error':{'code':503,'message':'Unavailable'}})
    page.route('https://openrouter.ai/api/v1/chat/completions',paid_error)
    page.locator('#ai-send').click()
    page.wait_for_function('Array.from(document.querySelectorAll(".ai-message.error")).some(e=>e.textContent.includes("temporarily unavailable"))')
    assert len(paid_calls)==1 and paid_calls[0]['model']=='openai/gpt-4o'
    print('PASS free retry, reasoning budget, structured content, paid opt-in, clean/undo notes, saved resize and empty-answer recovery')
    browser.close()
