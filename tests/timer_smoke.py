"""Timer controls, counting, persistence and focused practice UI."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from fixtures import seed_bank
with sync_playwright() as p:
    name=os.environ.get('TEST_BROWSER','chromium')
    kwargs={'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if name=='chromium' and Path('/usr/bin/chromium').exists() else {}
    browser=getattr(p,name).launch(**kwargs)
    page=browser.new_page();seed_bank(page)
    page.goto(os.environ.get('TEST_URL','http://127.0.0.1:8000'))
    assert page.locator('.bank-tools,#csv-import,.study-header').count()==0
    page.locator('#session-toggle').click()
    page.evaluate('sessionStarted -= 120000')
    page.locator('[data-choice="b"]').first.click()
    expect(page.locator('#session-count')).to_have_text('1')
    expect(page.locator('#session-time')).to_have_text('02:00')
    expect(page.locator('#session-pace')).to_have_text('02:00')
    page.locator('[data-action="retry"]').first.click()
    page.locator('[data-choice="a"]').first.click()
    expect(page.locator('#session-count')).to_have_text('1')
    page.locator('#session-toggle').click()
    page.locator('.question-card').nth(1).locator('[data-choice="b"]').click()
    expect(page.locator('#session-count')).to_have_text('1')
    page.reload()
    expect(page.locator('#session-toggle')).to_have_text('Resume')
    expect(page.locator('#session-count')).to_have_text('1')
    page.locator('#session-toggle').click()
    page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))")
    expect(page.locator('#session-toggle')).to_have_text('Resume')
    page.locator('#session-reset').click()
    expect(page.locator('#session-time')).to_have_text('00:00')
    expect(page.locator('#session-count')).to_have_text('0')
    assert page.evaluate('Object.keys(progress).length')>=2
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path='/tmp/practice-timer-mobile.png')
    page.close()
    # The compact timer must remain usable deep in the published bank, across sizes.
    for width in [320, 390, 834, 1440]:
        context=browser.new_context(viewport={'width':width,'height':900})
        page=context.new_page()
        page.goto(os.environ.get('TEST_URL','http://127.0.0.1:8000'))
        expect(page.locator('.question-card').first).to_be_visible()
        expect(page.locator('#session-dock')).to_be_hidden()
        page.locator('#session-toggle').click()
        page.evaluate('sessionStarted -= 125000; renderTimer()')
        page.locator('.question-card').nth(2).evaluate('(e)=>e.scrollIntoView({block:"start"})')
        expect(page.locator('#session-dock')).to_be_in_viewport()
        expect(page.locator('#session-dock-state')).to_have_text('Running')
        card_before=page.locator('.question-card').nth(2).bounding_box()['y']
        page.locator('#session-dock-toggle').click()
        expect(page.locator('#session-toggle')).to_have_text('Resume')
        expect(page.locator('#session-dock-state')).to_have_text('Paused')
        assert abs(page.locator('.question-card').nth(2).bounding_box()['y']-card_before)<2
        page.locator('#session-dock-toggle').click()
        page.locator('.question-card').nth(2).locator('[data-choice="b"]').click()
        expect(page.locator('#session-dock-count')).to_have_text('1')
        assert page.evaluate("['time','count','pace'].every(k=>document.getElementById('session-'+k).textContent===document.getElementById('session-dock-'+k).textContent)")
        dock=page.locator('#session-dock').bounding_box()
        nav=page.locator('.topbar').bounding_box()
        assert dock['y']>=nav['y']+nav['height']-1
        assert page.locator('#session-dock').evaluate('(e)=>e.scrollWidth<=e.clientWidth'),width
        if width==390:page.screenshot(path='/tmp/sticky-timer-mobile.png')
        if width==1440:
            page.locator('.question-card').nth(2).locator('[data-action="explain"]').click()
            page.locator('#tutor-resize').focus();page.keyboard.press('End')
            page.wait_for_function("Math.abs(document.getElementById('session-dock').getBoundingClientRect().width-document.querySelector('.topbar').getBoundingClientRect().width)<1")
            assert page.locator('#session-dock').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
            page.locator('#ai-close').click()
            page.wait_for_function("Math.abs(document.getElementById('session-dock').getBoundingClientRect().width-document.querySelector('.topbar').getBoundingClientRect().width)<1")
            page.screenshot(path='/tmp/sticky-timer-desktop.png')
        page.locator('#practice-top').click()
        expect(page.locator('#session-dock')).to_be_hidden()
        expect(page.locator('#session-toggle')).to_be_focused()
        assert page.evaluate('scrollY')==0
        page.locator('#session-reset').click()
        page.locator('.pagination').last.locator('[data-page="next"]').click()
        expect(page.locator('.question-number').first).to_have_text('Question 21')
        expect(page.locator('#session-dock')).to_be_in_viewport()
        page.wait_for_function("document.querySelector('.question-card').getBoundingClientRect().top >= document.getElementById('session-dock').getBoundingClientRect().bottom")
        expect(page.locator('#session-dock-time')).to_have_text('00:00')
        expect(page.locator('#session-dock-state')).to_have_text('Ready')
        page.locator('#session-dock-toggle').click()
        expect(page.locator('#session-dock-state')).to_have_text('Running')
        page.reload()
        page.locator('.question-card').nth(2).evaluate('(e)=>e.scrollIntoView({block:"start"})')
        expect(page.locator('#session-dock-state')).to_have_text('Paused')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
        context.close()
    browser.close()
    print('PASS timer controls, persistence, hidden-tab pause, scroll visibility at four widths, synchronized metrics, tutor resizing, pagination clearance and top navigation')
