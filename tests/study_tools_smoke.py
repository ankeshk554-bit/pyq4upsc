"""Portable backups, transactional merges, readable notes, DOCX and PDF print layout."""
import json,os,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from fixtures import seed_bank
URL=os.environ.get('TEST_URL','http://127.0.0.1:8000')
with sync_playwright() as p:
 name=os.environ.get('TEST_BROWSER','chromium');kwargs={'executable_path':'/usr/bin/chromium','args':['--no-sandbox']} if name=='chromium' and Path('/usr/bin/chromium').exists() else {}
 b=getattr(p,name).launch(**kwargs)
 page=b.new_page();seed_bank(page);page.goto(URL)
 page.locator('[data-choice="b"]').first.click()
 page.locator('[data-action="toggle-note"]').first.click()
 page.locator('[data-note-id]').first.fill('**Polity revision**\nArticle 17 abolishes untouchability. <script>bad()</script>')
 page.locator('#save-session').click()
 page.evaluate("localStorage.setItem('uv_ai_connection_v1_openai',JSON.stringify({key:'secret-must-not-export',model:'gpt-4o'}))")
 page.locator('.topbar .ai-settings-open').click()
 page.locator('#settings-tab-data').click()
 page.locator('#backup-open').click()
 with page.expect_download() as download:page.locator('#backup-download').click()
 file='/tmp/study-backup.json';download.value.save_as(file);data=json.loads(Path(file).read_text())
 assert 'secret-must-not-export' not in Path(file).read_text()
 assert data['progress']['demo-q-1']['selected']=='b' and len(data['history'])==1
 page.locator('[data-close="backup-dialog"]').click();page.reload()
 assert page.locator('[data-note-id]').first.input_value().startswith('**Polity')
 other=b.new_page();seed_bank(other);other.goto(URL)
 other.locator('[data-action="toggle-note"]').first.click();other.locator('[data-note-id]').first.fill('Local note to preserve')
 other.locator('.topbar .ai-settings-open').click()
 other.locator('#settings-tab-data').click()
 other.locator('#backup-open').click();other.locator('#backup-file').set_input_files(file)
 expect(other.locator('#backup-merge')).to_be_enabled();other.locator('#backup-merge').click()
 expect(other.locator('#backup-preview')).to_contain_text('merged and saved')
 other.locator('[data-close="backup-dialog"]').click();other.reload()
 assert 'Local note to preserve' in other.locator('[data-note-id]').first.input_value()
 assert 'Article 17' in other.locator('[data-note-id]').first.input_value()
 assert other.evaluate("progress['demo-q-1'].selected")=='b'
 other.locator('#notes-open').click();other.locator('#notes-subject').select_option('Polity')
 expect(other.locator('#notes-count')).to_have_text('1 note')
 assert other.locator('#notes-reader script').count()==0
 other.locator('[data-close="notes-dialog"]').click()
 other.locator('.topbar .ai-settings-open').click()
 other.locator('#notes-size').select_option('23')
 other.locator('#ai-settings-done').click()
 other.locator('#notes-open').click()
 other.locator('#notes-reader button').click();other.locator('#notes-reader textarea').fill('Edited revision: Article 17.');other.locator('#notes-reader button').click()
 with other.expect_download() as download:other.locator('#notes-word').click()
 doc='/tmp/revision-notes.docx';download.value.save_as(doc)
 with zipfile.ZipFile(doc) as z:
  assert z.testzip() is None
  for name in z.namelist():ET.fromstring(z.read(name))
  assert 'Edited revision: Article 17.' in z.read('word/document.xml').decode()
 other.evaluate('window.print=()=>{window.printRequested=true}')
 other.locator('#notes-pdf').click();assert other.evaluate('window.printRequested')
 other.emulate_media(media='print');expect(other.locator('#notes-print')).to_be_visible();expect(other.locator('.app-shell')).to_be_hidden()
 assert 'Edited revision' in other.locator('#notes-print').inner_text();other.emulate_media(media='screen')
 # Invalid backup and failed storage must leave existing state intact.
 other.locator('.topbar .ai-settings-open').click()
 other.locator('#settings-tab-data').click()
 other.locator('#backup-open').click()
 other.locator('#backup-file').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'{"version":900}'})
 expect(other.locator('#backup-merge')).to_be_disabled()
 before=other.evaluate('JSON.stringify(progress)')
 other.locator('#backup-file').set_input_files(file);expect(other.locator('#backup-merge')).to_be_enabled()
 other.evaluate("window.originalSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==='uv_study_v1')throw new DOMException('Full','QuotaExceededError');return window.originalSet.call(this,k,v)};void 0")
 other.locator('#backup-merge').click();expect(other.locator('#backup-preview')).to_contain_text('could not be saved')
 assert other.evaluate('JSON.stringify(progress)')==before
 other.locator('[data-close="backup-dialog"]').click()
 other.evaluate("progress['demo-q-1'].note='Unsaved note';saveProgress()")
 expect(other.locator('#save-status')).to_contain_text('Not saved')
 other.evaluate('Storage.prototype.setItem=window.originalSet;void 0')
 page.set_viewport_size({'width':390,'height':844});page.locator('#notes-open').click()
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 page.screenshot(path='/tmp/notes-library-mobile.png')
 # A second tab's save must not be overwritten silently.
 page.evaluate("localStorage.setItem('uv_study_v1',JSON.stringify({...studySnapshot(),exportedAt:'changed elsewhere'}));persistStudy()")
 expect(page.locator('#save-status')).to_contain_text('Changed in another tab')
 b.close();print('PASS backup transfer, merged notes, refresh, secret exclusion, reader editing, valid DOCX, PDF layout, invalid backup and atomic quota failure')
