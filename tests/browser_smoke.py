import os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page(); errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(os.environ.get('TEST_URL', 'http://127.0.0.1:8000'),wait_until='networkidle')
 assert page.locator('.question-card').count()==10
 page.locator('[data-action="reveal"][data-qid="demo-q-1"]').click()
 assert page.locator('article[data-qid="demo-q-1"] .badge').filter(has_text='Answer revealed').count()==1
 assert page.locator('article[data-qid="demo-q-1"] .option.correct').count()==1
 assert page.locator('.option.selected').count()==0
 page.locator('[data-choice="b"][data-qid="demo-q-1"]').click()
 assert page.locator('article[data-qid="demo-q-1"] .option.selected').count()==1
 assert '100%' in page.locator('#stats-summary').inner_text()
 assert page.locator('#stats-bar .stat').nth(2).locator('strong').inner_text()=='1'
 page.locator('[data-action="toggle-mark"][data-qid="demo-q-1"]').click()
 page.locator('#marked-filter').click(); assert page.locator('.question-card').count()==1
 page.locator('[data-action="toggle-mark"][data-qid="demo-q-1"]').click()
 assert page.locator('.question-card').count()==0
 page.locator('#reset-filters').click()
 before=page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')
 page.locator('#theme-toggle').click()
 assert before!=page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')
 page.locator('[data-action="toggle-note"][data-qid="demo-q-1"]').click()
 page.locator('[data-note-id="demo-q-1"]').fill('Remember Article 17')
 page.reload(); assert page.locator('[data-note-id="demo-q-1"]').input_value()=='Remember Article 17'
 page.locator('#save-session').click()
 assert '1/1' in page.locator('#history-list').inner_text()
 page.reload(); assert '1/1' in page.locator('#history-list').inner_text()
 print('PASS reveal, answers, live statistics, marking/filter, theme, notes and session persistence')
 page.locator('#csv-upload').set_input_files({'name':'valid.csv','mimeType':'text/csv','buffer':b'Question,Subject,Year,Official Answer Key\n"Which, article?\n(a) 15 (b) 17",Polity,2025,(b)\n'})
 assert page.locator('.question-card').count()==1
 assert 'Which, article?' in page.locator('.question-stem').inner_text()
 page.locator('#csv-upload').set_input_files({'name':'invalid.csv','mimeType':'text/csv','buffer':b'Question,Official Answer Key\nInvalid,z\n'})
 assert page.locator('.question-card').count()==1
 assert 'Invalid' in page.locator('#notice').inner_text()
 print('PASS multiline CSV and invalid import preserves bank')
 page.locator('[data-action="explain"]').click(); page.locator('#ai-send').click()
 page.locator('.ai-message.error').wait_for()
 assert 'not connected' in page.locator('.ai-message.error').inner_text()
 assert page.locator('#ai-send').is_enabled()
 page.locator('#ai-close').click()
 requests=[]
 def reply(route):
  requests.append(route.request.post_data_json)
  route.fulfill(json={'reply':'Article 17 abolishes untouchability. <script>never execute</script>'})
 page.route('**/api/explain',reply)
 page.locator('[data-action="explain"]').click(); page.locator('#ai-send').click()
 page.locator('.ai-message.assistant').wait_for()
 assert page.locator('#ai-messages script').count()==0
 page.locator('#ai-question').fill('What about Article 15?'); page.locator('#ai-send').click()
 page.wait_for_function('document.querySelectorAll(".ai-message.assistant").length === 2')
 assert len(requests[-1]['messages'])==3
 assert requests[-1]['answer']=='b'
 page.locator('#ai-close').click()
 print('PASS AI missing-key state, question context, follow-up history, safe text rendering (mocked responses)')
 page.set_viewport_size({'width':390,'height':844})
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 page.screenshot(path='/tmp/upsc-mobile.png',full_page=True)
 page.set_viewport_size({'width':1440,'height':900})
 page.screenshot(path='/tmp/upsc-desktop.png',full_page=True)
 assert not errors,errors
 print('PASS mobile overflow and no page errors')
 b.close()
