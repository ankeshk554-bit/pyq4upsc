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
    browser.close()
    print('PASS timer start/pause/reset, unique counts, average, paused refresh, hidden-tab pause and mobile overflow')
