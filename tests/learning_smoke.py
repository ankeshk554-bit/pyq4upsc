"""Fresh-start, large-bank navigation, revision, and saved learning notes."""
import csv
import io
import os
from playwright.sync_api import sync_playwright
def publish(page, file):
 page.unroute('**/data/questions.csv')
 page.route('**/data/questions.csv',lambda r:r.fulfill(body=file['buffer'],content_type='text/csv'))
 page.evaluate('loadPublishedBank()')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page()
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.route('**/data/questions.csv', lambda r:r.fulfill(status=404))
    page.goto(os.environ.get('TEST_URL','http://127.0.0.1:8000'))
    assert page.locator('#sample-load').count()==0
    assert page.locator('.question-card').count()==0
    assert page.locator('#questions-retry').is_visible()
    csvfile=io.StringIO();writer=csv.writer(csvfile)
    writer.writerow(['Question','Subject','Year','Official Answer Key'])
    for i in range(45): writer.writerow([f'Practice question {i+1}? (a) One (b) Two','Polity',2024,'b'])
    publish(page, {'name':'bank.csv','mimeType':'text/csv','buffer':csvfile.getvalue().encode()})
    page.wait_for_function('allQuestions.length===45')
    assert page.locator('.question-card').count()==20
    page.locator('[data-page="next"]').first.click()
    assert 'Practice question 21?' in page.locator('.question-stem').first.inner_text()
    page.locator('[data-page="next"]').first.click()
    assert page.locator('.question-card').count()==5
    assert page.locator('[data-page="next"]').first.is_disabled()
    page.locator('#search-input').fill('Practice question 1?');page.wait_for_timeout(300)
    assert page.locator('.question-card').count()==1
    page.locator('[data-choice="a"]').click()
    assert page.locator('[data-choice="b"]').is_disabled()
    page.locator('[data-action="toggle-mark"]').click()
    page.locator('[data-action="toggle-note"]').click()
    page.locator('[data-note-id]').fill('My revision note')
    page.locator('#reset-filters').click()
    page.locator('#study-view').select_option('mistakes')
    assert page.locator('.question-card').count()==1
    page.locator('[data-action="retry"]').click()
    assert page.locator('[data-choice="b"]').is_enabled()
    assert page.locator('[data-note-id]').input_value()=='My revision note'
    assert page.locator('[data-action="toggle-mark"]').inner_text()=='Unmark'
    page.locator('[data-choice="b"]').click()
    page.route('**/api/explain',lambda route:route.fulfill(json={'reply':'**Remember:** A short learning takeaway.'}))
    page.locator('[data-action="explain"]').click();page.locator('#ai-send').click()
    page.locator('.save-ai-note').click()
    assert 'A short learning takeaway.' in page.locator('[data-note-id]').input_value()
    assert 'My revision note' in page.locator('[data-note-id]').input_value()
    page.locator('#ai-close').click()
    page.locator('#study-view').select_option('unanswered')
    assert page.locator('#stats-bar .stat').nth(1).locator('strong').inner_text()=='44'
    page.reload()
    assert 'A short learning takeaway.' in page.locator('[data-note-id]').first.input_value()
    assert not errors,errors
    print('PASS fresh CSV start, bounded pages, search reset, mistakes/unanswered views, retry preserves notes/bookmarks, AI notes persist')
    browser.close()
