"""Tablet portrait/landscape flows on Chromium or WebKit; synthetic API replies."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from fixtures import seed_bank

with sync_playwright() as p:
    name=os.environ.get('TEST_BROWSER','chromium')
    kwargs={}
    if name=='chromium' and Path('/usr/bin/chromium').exists():
        kwargs={'executable_path':'/usr/bin/chromium','args':['--no-sandbox']}
    browser=getattr(p,name).launch(**kwargs)
    for width,height in [(834,1194),(1194,834),(820,1180),(1180,820),(834,1210),(1210,834),(744,1133)]:
        context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=2,is_mobile=True,has_touch=True)
        page=context.new_page();seed_bank(page)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(os.environ.get('TEST_URL','http://127.0.0.1:8000'))
        expect(page.locator('#question-sidebar')).to_be_hidden()
        expect(page.locator('#filters-toggle')).to_have_attribute('aria-expanded','false')
        page.locator('#filters-toggle').tap()
        expect(page.locator('#question-sidebar')).to_be_visible()
        page.locator('#search-input').fill('untouchability')
        expect(page.locator('.question-card')).to_have_count(1)
        page.locator('#sidebar-close').tap()
        expect(page.locator('#question-sidebar')).to_be_hidden()
        page.locator('[data-choice="b"]').tap()
        expect(page.locator('.badge.good')).to_have_text('Correct')
        page.route('**/api/explain',lambda route:route.fulfill(json={'reply':'## Answer\n\n**Article 17** abolishes untouchability.\n\n| Article | Topic |\n|---|---|\n| 17 | Untouchability |'}))
        page.locator('[data-action="explain"]').tap()
        page.locator('#ai-send').tap()
        expect(page.locator('.ai-message.assistant table')).to_be_visible()
        if width>900:
            card=page.locator('.question-card').bounding_box();tutor=page.locator('#ai-dialog').bounding_box()
            assert card['x']+card['width']<=tutor['x'],(name,width,'overlap')
        assert page.locator('#ai-close').bounding_box()['width']>=44
        assert page.locator('#ai-question').evaluate('(e)=>getComputedStyle(e).fontSize')=='16px'
        page.locator('#ai-dialog .ai-settings-open').tap()
        expect(page.locator('#ai-settings-dialog')).to_be_visible()
        page.locator('#ai-provider').select_option('deepseek')
        page.locator('#ai-key').fill('synthetic-tablet-key');page.locator('#ai-remember').check()
        page.locator('#ai-settings-form button[type="submit"]').tap()
        page.locator('#ai-settings-done').tap()
        page.reload()
        expect(page.locator('#question-sidebar')).to_be_hidden()
        page.locator('.topbar .ai-settings-open').tap()
        expect(page.locator('#ai-provider')).to_have_value('deepseek')
        expect(page.locator('#ai-remember')).to_be_checked()
        page.locator('#ai-settings-done').tap()
        # Rotate and simulate the reduced viewport available above a software keyboard.
        page.set_viewport_size({'width':height,'height':width})
        page.locator('[data-action="explain"]').first.tap()
        page.set_viewport_size({'width':height,'height':450})
        page.wait_for_function('parseFloat(document.documentElement.style.getPropertyValue("--visual-height")) <= 450')
        send=page.locator('#ai-send').bounding_box()
        assert send['y']+send['height']<=451,(name,width,send)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(name,width,'overflow')
        assert not errors,errors
        context.close()
    # Desktop can also hide the sidebar and remember its collapsed preference.
    page=browser.new_page(viewport={'width':1440,'height':1000});seed_bank(page)
    page.goto(os.environ.get('TEST_URL','http://127.0.0.1:8000'))
    expect(page.locator('#question-sidebar')).to_be_visible()
    page.locator('#filters-toggle').click();page.reload()
    expect(page.locator('#question-sidebar')).to_be_hidden()
    page.locator('#filters-toggle').click()
    expect(page.locator('#question-sidebar')).to_be_visible()
    print(f'PASS {name}: seven iPad viewports, touch filters, answers, formatted tutor, settings, remembered keys, rotation, reduced viewport and desktop sidebar preference')
    browser.close()
