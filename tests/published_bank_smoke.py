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
    # Updated published content automatically replaces the cached question list.
    page.unroute('**/data/questions.csv')
    page.route('**/data/questions.csv',lambda r:r.fulfill(body=CSV.replace('Published question','New edition'),content_type='text/csv'))
    page.reload()
    expect(page.locator('.question-stem')).to_contain_text('New edition')
    assert page.locator('#csv-import, .bank-tools').count() == 0
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
        expect(fresh.locator('#questions-retry')).to_be_visible()
        fresh.unroute('**/data/questions.csv')
        fresh.route('**/data/questions.csv',lambda r:r.fulfill(body=CSV,content_type='text/csv'))
        fresh.locator('#questions-retry').click()
        expect(fresh.locator('.question-stem')).to_contain_text('Published question')
        fresh.close()
    browser.close()
    print('PASS published bank first visit, reload/progress persistence, automatic updates, new edition and retry after download failure')
