/* Local study persistence, portable backups and accessible note exports. No network calls. */
const STUDY_KEY = 'uv_study_v1';
let studyQuestions = new Map(), savedStates = new Map(), pendingBackup = null, lastStoredStudy = null, corruptStudy = false;
const cleanQuestion = q => ({id:q.id, question:q.question, subject:q.subject, year:q.year, ans:q.ans});
function stampProgress() {
  for (const [id,state] of Object.entries(progress)) {
    const encoded = JSON.stringify(state);
    if (savedStates.get(id) !== encoded) {
      const before = JSON.parse(savedStates.get(id) || '{}');
      state.updatedAt = Date.now();
      if (['selected','correct','revealed'].some(k=>before[k] !== state[k])) state.answerUpdatedAt = state.updatedAt;
      if (before.note !== state.note) state.noteUpdatedAt = state.updatedAt;
    }
    savedStates.set(id, JSON.stringify(state));
  }
}
function studySnapshot() {
  allQuestions.forEach(q => studyQuestions.set(q.id, cleanQuestion(q)));
  return {format:'upsc-vault-study', version:1, exportedAt:new Date().toISOString(), questions:[...studyQuestions.values()], bank:allQuestions.map(q=>q.id), progress, history};
}
function savedStatus(ok) {
  const node = document.getElementById('save-status');
  node.textContent = ok ? 'Saved on this device · Back up' : 'Not saved — download a backup now';
  node.classList.toggle('unsaved', !ok);
}
function persistStudy() {
  try {
    if (corruptStudy) { savedStatus(false); return false; }
    if (localStorage.getItem(STUDY_KEY) !== lastStoredStudy) {
      savedStatus(false); document.getElementById('save-status').textContent = 'Changed in another tab — back up this tab, then reload'; return false;
    }
    const encoded = JSON.stringify(studySnapshot());
    localStorage.setItem(STUDY_KEY, encoded); lastStoredStudy = encoded;
    // Migrate older separate records only after the complete snapshot succeeds.
    for (const key of [STORAGE_KEYS.bank, STORAGE_KEYS.progress, STORAGE_KEYS.history]) localStorage.removeItem(key);
    savedStatus(true); return true;
  } catch { savedStatus(false); return false; }
}
function validBackup(raw) {
  const fail = () => { throw new Error('This is not a valid UPSC Vault study backup. Nothing has been changed.'); };
  if (!raw || raw.format !== 'upsc-vault-study' || raw.version !== 1 || !Array.isArray(raw.questions) || raw.questions.length > 20000 || !raw.progress || typeof raw.progress !== 'object' || Array.isArray(raw.progress) || !Array.isArray(raw.history) || raw.history.length > 10000) fail();
  const questions = [], ids = new Set();
  const validId = id => typeof id === 'string' && id.length > 0 && id.length <= 200 && !['__proto__','prototype','constructor'].includes(id);
  for (const q of raw.questions) {
    if (!q || !validId(q.id) || ids.has(q.id) || typeof q.question !== 'string' || !q.question.trim() || q.question.length > 30000 || typeof q.subject !== 'string' || q.subject.length > 300 || !Number.isFinite(q.year) || !['','a','b','c','d'].includes(q.ans)) fail();
    ids.add(q.id); questions.push(cleanQuestion(q));
  }
  const states = Object.create(null);
  if (Object.keys(raw.progress).length > 30000) fail();
  for (const [id,state] of Object.entries(raw.progress)) {
    if (!validId(id) || !state || typeof state !== 'object' || Array.isArray(state)) fail();
    const copy = {};
    for (const field of ['marked','revealed','correct']) if (state[field] !== undefined) { if (typeof state[field] !== 'boolean') fail(); copy[field] = state[field]; }
    if (state.selected !== undefined) { if (!['a','b','c','d'].includes(state.selected)) fail(); copy.selected = state.selected; }
    if (state.note !== undefined) { if (typeof state.note !== 'string' || state.note.length > 1000000) fail(); copy.note = state.note; }
    if (state.image !== undefined) { if (typeof state.image !== 'string' || state.image.length > 6000000 || !/^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$/.test(state.image)) fail(); copy.image = state.image; }
    for (const field of ['updatedAt','answerUpdatedAt','noteUpdatedAt']) if (state[field] !== undefined) { if (!Number.isFinite(state[field]) || state[field] < 0 || state[field] > Date.now()+86400000) fail(); copy[field] = state[field]; }
    states[id] = copy;
  }
  const records = raw.history.map(h => {
    if (!h || typeof h.date !== 'string' || !Number.isFinite(Date.parse(h.date)) || typeof h.score !== 'string' || !/^\d+\/\d+$/.test(h.score) || !Number.isFinite(h.accuracy) || h.accuracy < 0 || h.accuracy > 100) fail();
    return {testId:Number.isFinite(h.testId) ? h.testId : 0, date:h.date, score:h.score, accuracy:h.accuracy};
  });
  if (!Array.isArray(raw.bank) || raw.bank.some(id => !ids.has(id))) fail();
  return {format:raw.format, version:1, exportedAt:typeof raw.exportedAt === 'string' ? raw.exportedAt : '', questions, bank:[...new Set(raw.bank)], progress:states, history:records};
}
function restoreStudy() {
  const encoded = safeGet(STUDY_KEY); lastStoredStudy = encoded;
  if (encoded) {
    try {
      const data = validBackup(JSON.parse(encoded));
      studyQuestions = new Map(data.questions.map(q=>[q.id,q]));
      allQuestions = data.bank.map(id=>normalizeQuestion(studyQuestions.get(id)));
      progress = data.progress; history = data.history;
    } catch { corruptStudy = true; notify('Saved study data could not be read. Restore a backup before continuing.'); savedStatus(false); }
  }
  allQuestions.forEach(q=>studyQuestions.set(q.id, cleanQuestion(q)));
  savedStates = new Map(Object.entries(progress).map(([id,state])=>[id,JSON.stringify(state)]));
}
function downloadStudyFile(blob, name) {
  const url = URL.createObjectURL(blob), link = document.createElement('a');
  link.href = url; link.download = name; document.body.append(link); link.click(); link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),60000);
}
function mergeNotes(local, incoming) {
  if (!local) return incoming || '';
  if (!incoming || local === incoming || local.includes(incoming)) return local;
  if (incoming.includes(local)) return incoming;
  return `${local}\n\n— Note from restored backup —\n\n${incoming}`;
}
function mergeStudy(data) {
  stampProgress();
  const merged = Object.assign(Object.create(null), progress);
  const questions = new Map(studyQuestions);
  allQuestions.forEach(q=>questions.set(q.id,cleanQuestion(q)));
  for (const q of data.questions) if (!questions.has(q.id)) questions.set(q.id,q);
  for (const [id,incoming] of Object.entries(data.progress)) {
    const local = progress[id];
    if (!local) { merged[id] = {...incoming}; continue; }
    const newer = (incoming.updatedAt || 0) > (local.updatedAt || 0) ? incoming : local;
    merged[id] = {...newer, note:mergeNotes(local.note,incoming.note), marked:!!(local.marked || incoming.marked)};
    const answerTime = s => s.answerUpdatedAt || ((s.selected || s.revealed) ? s.updatedAt || 0 : 0);
    const answer = answerTime(incoming) > answerTime(local) || (!local.selected && !local.answerUpdatedAt && incoming.selected) ? incoming : local;
    for (const key of ['selected','correct','revealed','answerUpdatedAt']) { delete merged[id][key]; if (answer[key] !== undefined) merged[id][key] = answer[key]; }
    if (!merged[id].image && (local.image || incoming.image)) merged[id].image = local.image || incoming.image;
    merged[id].updatedAt = Math.max(local.updatedAt || 0, incoming.updatedAt || 0);
  }
  // Recompute grading from the current bank instead of trusting exported correctness.
  for (const [id,state] of Object.entries(merged)) {
    const q = questions.get(id);
    if (q && state.selected) { if (q.ans) state.correct = q.ans === state.selected; else delete state.correct; }
  }
  const records = [...new Map([...history,...data.history].map(h=>[`${h.date}|${h.score}|${h.accuracy}`,h])).values()].sort((a,b)=>Date.parse(b.date)-Date.parse(a.date));
  const bank = allQuestions.length ? allQuestions : data.bank.map(id=>normalizeQuestion(questions.get(id)));
  const snapshot = {format:'upsc-vault-study',version:1,exportedAt:new Date().toISOString(),questions:[...questions.values()],bank:bank.map(q=>q.id),progress:merged,history:records};
  // A single storage write commits the restore. Failure leaves active data untouched.
  if (localStorage.getItem(STUDY_KEY) !== lastStoredStudy) throw new Error('Another tab changed study data.');
  const encoded = JSON.stringify(snapshot);
  localStorage.setItem(STUDY_KEY,encoded); lastStoredStudy = encoded; corruptStudy = false;
  studyQuestions = questions; allQuestions = bank; progress = merged; history = records;
  savedStates = new Map(Object.entries(progress).map(([id,state])=>[id,JSON.stringify(state)]));
  savedStatus(true); renderFilters(); applyFilters(); buildStatsSummary(); renderHistory();
}
function visibleNotes() {
  allQuestions.forEach(q=>studyQuestions.set(q.id,cleanQuestion(q)));
  const subject = document.getElementById('notes-subject').value;
  const search = document.getElementById('notes-search').value.trim().toLowerCase();
  return [...studyQuestions.values()].filter(q=>typeof progress[q.id]?.note === 'string' && progress[q.id].note.trim() && (!subject || q.subject === subject) && (!search || `${q.question} ${progress[q.id].note}`.toLowerCase().includes(search))).sort((a,b)=>a.subject.localeCompare(b.subject) || b.year-a.year || a.id.localeCompare(b.id));
}
function noteArticle(q, editable = false) {
  const article = document.createElement('article'); article.className = 'reading-note';
  const heading = document.createElement('h3'); heading.textContent = `${q.subject} · ${q.year || 'Year unavailable'}`;
  const question = document.createElement('div'); question.className = 'reading-question'; question.textContent = q.question;
  const body = document.createElement('div'); body.className = 'reading-body'; body.textContent = tutorPlainText(progress[q.id].note);
  article.append(heading,question,body);
  const image = progress[q.id].image;
  if (typeof image === 'string' && /^data:image\/(jpeg|png|webp);base64,/.test(image)) { const img=document.createElement('img');img.src=image;img.alt='Question attachment';article.append(img); }
  if (editable) {
    const button=document.createElement('button');button.textContent='Edit note';button.style.marginTop='16px';
    button.onclick=()=>{
      if (article.querySelector('textarea')) return;
      const input=document.createElement('textarea');input.value=progress[q.id].note;input.setAttribute('aria-label',`Edit ${q.subject} note`);
      const done=document.createElement('button');done.textContent='Done';
      input.oninput=()=>{progress[q.id].note=input.value;saveProgress();buildStatsSummary();};
      done.onclick=()=>{renderNoteLibrary();renderQuestions();};
      body.replaceWith(input);button.replaceWith(done);input.focus();
    };
    article.append(button);
  }
  return article;
}
function renderNoteLibrary() {
  const items=visibleNotes(),root=document.getElementById('notes-reader');root.replaceChildren();
  document.getElementById('notes-count').textContent=`${items.length} ${items.length===1?'note':'notes'}`;
  document.getElementById('notes-pdf').disabled=document.getElementById('notes-word').disabled=!items.length;
  if (!items.length) { const p=document.createElement('p');p.textContent='No notes in this view. Add a note to a question or save a tutor explanation, then return here.';root.append(p); }
  items.forEach(q=>root.append(noteArticle(q,true)));
}
function exportPrintNotes() {
  const root=document.getElementById('notes-print');root.replaceChildren();
  const heading=document.createElement('h1');heading.textContent='UPSC Vault · Revision notes';root.append(heading);
  let subject='';for(const q of visibleNotes()) { if(subject!==q.subject) {subject=q.subject;const h=document.createElement('h2');h.textContent=subject;root.append(h);} root.append(noteArticle(q)); }
  document.getElementById('notes-dialog').close();
  window.print();
}
// Minimal standards-compliant DOCX (ZIP container with UTF-8 WordprocessingML).
function wordDocument(items) {
  const xml = text => String(text).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g,'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
  const para=(text,bold=false)=>`<w:p><w:r>${bold?'<w:rPr><w:b/></w:rPr>':''}<w:t xml:space="preserve">${xml(text)}</w:t></w:r></w:p>`;
  let body=para('UPSC Vault · Revision notes',true),subject='';
  for(const q of items) { if(subject!==q.subject) {subject=q.subject;body+=para(subject,true);} body+=para(String(q.year || ''),true); for(const line of q.question.split('\n')) body+=para(line); for(const line of tutorPlainText(progress[q.id].note).split('\n')) body+=para(line); if(progress[q.id].image) body+=para('[Question attachment: included in PDF and study backup]'); body+=para(''); }
  const files=[['[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'],['_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'],['word/document.xml',`<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>${body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/></w:sectPr></w:body></w:document>`]];
  const encoder=new TextEncoder(), chunks=[],central=[];let offset=0,size=0;
  const header=(length)=>{const bytes=new Uint8Array(length);return {bytes,view:new DataView(bytes.buffer)};};
  for(const [name,text] of files) {
    const n=encoder.encode(name),data=encoder.encode(text);let crc=0xffffffff;
    for(const b of data) {crc^=b;for(let i=0;i<8;i++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);}crc=(crc^0xffffffff)>>>0;
    const h=header(30);h.view.setUint32(0,0x04034b50,true);h.view.setUint16(4,20,true);h.view.setUint32(14,crc,true);h.view.setUint32(18,data.length,true);h.view.setUint32(22,data.length,true);h.view.setUint16(26,n.length,true);chunks.push(h.bytes,n,data);
    const c=header(46);c.view.setUint32(0,0x02014b50,true);c.view.setUint16(4,20,true);c.view.setUint16(6,20,true);c.view.setUint32(16,crc,true);c.view.setUint32(20,data.length,true);c.view.setUint32(24,data.length,true);c.view.setUint16(28,n.length,true);c.view.setUint32(42,offset,true);central.push(c.bytes,n);size+=46+n.length;offset+=30+n.length+data.length;
  }
  const end=header(22);end.view.setUint32(0,0x06054b50,true);end.view.setUint16(8,files.length,true);end.view.setUint16(10,files.length,true);end.view.setUint32(12,size,true);end.view.setUint32(16,offset,true);
  return new Blob([...chunks,...central,end.bytes],{type:'application/vnd.openxmlformats-officedocument.wordprocessingml.document'});
}
function bindStudyTools() {
  document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>document.getElementById(b.dataset.close).close());
  document.getElementById('notes-open').onclick=()=>{
    allQuestions.forEach(q=>studyQuestions.set(q.id,cleanQuestion(q)));
    const select=document.getElementById('notes-subject'),previous=select.value;select.replaceChildren(new Option('All subjects',''));
    [...new Set([...studyQuestions.values()].filter(q=>progress[q.id]?.note?.trim()).map(q=>q.subject))].sort().forEach(s=>select.add(new Option(s,s)));
    if([...select.options].some(o=>o.value===previous))select.value=previous;
    document.getElementById('notes-options').open = window.innerWidth > 700;
    renderNoteLibrary();document.getElementById('notes-dialog').showModal();
  };
  document.getElementById('notes-subject').onchange=renderNoteLibrary;
  document.getElementById('notes-search').oninput=renderNoteLibrary;
  document.getElementById('notes-size').onchange=e=>document.getElementById('notes-reader').style.setProperty('--reading-size',`${e.target.value}px`);
  document.getElementById('notes-pdf').onclick=exportPrintNotes;
  document.getElementById('notes-word').onclick=()=>downloadStudyFile(wordDocument(visibleNotes()),'upsc-revision-notes.docx');
  let backupReturnFocus;
  const openBackup = event => {
    const settings = document.getElementById('ai-settings-dialog');
    backupReturnFocus = settings.open ? document.querySelector('.topbar .ai-settings-open') : event.currentTarget;
    if (settings.open) settings.close();
    document.getElementById('backup-dialog').showModal();
  };
  document.getElementById('backup-open').onclick = openBackup;
  document.getElementById('backup-status').onclick = openBackup;
  document.getElementById('backup-dialog').addEventListener('close', () => backupReturnFocus?.focus());
  document.getElementById('backup-download').onclick=()=>{
    stampProgress();downloadStudyFile(new Blob([JSON.stringify(studySnapshot(),null,2)],{type:'application/json'}),`upsc-study-${new Date().toISOString().slice(0,10)}.json`);
    document.getElementById('backup-last').textContent='Backup download requested. Keep the file somewhere you can access on your other device.';
  };
  document.getElementById('backup-file').onchange=async e=>{
    const file=e.target.files[0];pendingBackup=null;document.getElementById('backup-merge').disabled=true;
    if(!file)return;
    try {if(file.size>25*1024*1024)throw new Error('Backup exceeds the 25 MB limit.');pendingBackup=validBackup(JSON.parse(await file.text()));
      const states=Object.values(pendingBackup.progress);
      document.getElementById('backup-preview').textContent=`Ready to merge: ${states.filter(s=>s.selected).length} answered questions, ${states.filter(s=>s.note?.trim()).length} notes, ${pendingBackup.history.length} score snapshots. Existing work will be preserved.`;
      document.getElementById('backup-merge').disabled=false;
    } catch(error) {document.getElementById('backup-preview').textContent=error instanceof SyntaxError?'This file is not valid JSON. Nothing has changed.':error.message;}
  };
  document.getElementById('backup-merge').onclick=()=>{
    if(!pendingBackup)return;
    try {mergeStudy(pendingBackup);pendingBackup=null;document.getElementById('backup-merge').disabled=true;document.getElementById('backup-preview').textContent='Backup merged and saved on this device. Your notes are available in the Notes library.';}
    catch {document.getElementById('backup-preview').textContent='The backup could not be saved, possibly because storage is full or another tab saved changes. Your existing study data is unchanged. Download a backup of this device before freeing space.';}
  };
  document.addEventListener('visibilitychange',()=>{if(document.hidden)persistStudy();});
}
