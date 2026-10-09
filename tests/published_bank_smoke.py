"""Published CSV bootstrap and local bank persistence; no private question data."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

CSV='Question,Subject,Year,Official Answer Key\n"Published question? (a) One (b) Two",Polity,2025,b\n'
with sync_playwright() as p:
    name=os.environ.get('TEST_BROWSER','chromium')
    kwargs={'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if name=='chromium' and Path('/usr/bin/chromium').exists() else {}
    browser=getattr(p,name).launch(**kwargs)
    page=browser.new_page()
    page.route('**/data/questions.csv',lambda r:r.fulfill(body=CSV,content_type='text/csv'))
    page.goto(os.environ.get('TEST_URL','http://127.0.0.1:8000'))
    expect(page.locator('.question-card')).to_have_count(1)
    expect(page.locator('.question-stem')).to_contain_text('Published question')
    page.locator('[data-choice="b"]').click()
    page.reload()
    expect(page.locator('.question-card')).to_contain_text('Correct')
    # Updating the hosted file must not replace a visitor's local bank.
    page.unroute('**/data/questions.csv')
    page.route('**/data/questions.csv',lambda r:r.fulfill(body=CSV.replace('Published question','New edition'),content_type='text/csv'))
    page.reload()
    expect(page.locator('.question-stem')).to_contain_text('Published question')
    # A new browser profile receives the newly published edition.
    fresh=browser.new_page()
    fresh.route('**/data/questions.csv',lambda r:r.fulfill(body=CSV.replace('Published question','New edition'),content_type='text/csv'))
    fresh.goto(os.environ.get('TEST_URL','http://127.0.0.1:8000'))
    expect(fresh.locator('.question-stem')).to_contain_text('New edition')
    fresh.close()
    for status,body in [(404,''),(200,'not a csv'),(503,'Unavailable')]:
        fresh=browser.new_page()
        fresh.route('**/data/questions.csv',lambda r:r.fulfill(status=status,body=body))
        fresh.goto(os.environ.get('TEST_URL','http://127.0.0.1:8000'))
        expect(fresh.locator('#empty-import')).to_be_visible()
        fresh.locator('#csv-upload').set_input_files({'name':'bank.csv','mimeType':'text/csv','buffer':CSV.encode()})
        expect(fresh.locator('.question-stem')).to_contain_text('Published question')
        fresh.close()
    browser.close()
    print('PASS published bank first visit, reload/progress persistence, local precedence, new edition and import after download failure')
