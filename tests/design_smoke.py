"""Reading-room layout, filter removal, note controls and retained appearance preferences."""
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from fixtures import seed_bank
URL = os.environ.get('TEST_URL', 'http://127.0.0.1:8000')

def contrast(foreground, background):
    def luminance(color):
        channels = [int(value) / 255 for value in re.findall(r'\d+', color)[:3]]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return sum(value * weight for value, weight in zip(linear, [0.2126, 0.7152, 0.0722]))
    light, dark = sorted([luminance(foreground), luminance(background)], reverse=True)
    return (light + 0.05) / (dark + 0.05)

with sync_playwright() as p:
    name = os.environ.get('TEST_BROWSER', 'chromium')
    launch_options = {'executable_path':'/usr/bin/chromium', 'args':['--no-sandbox']} if name == 'chromium' and Path('/usr/bin/chromium').exists() else {}
    browser = getattr(p, name).launch(**launch_options)
    page = browser.new_page(viewport={'width':1440,'height':1000})
    seed_bank(page)
    errors=[]
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(URL)
    expect(page.locator('html')).to_have_attribute('data-theme','paper')
    assert 'Georgia' in page.locator('.question-stem').first.evaluate('(e)=>getComputedStyle(e).fontFamily')
    page.locator('[data-year="2024"]').click()
    page.locator('[data-subject="Polity"]').click()
    expect(page.locator('.question-card')).to_have_count(1)
    expect(page.locator('[data-subject="Polity"]')).to_have_attribute('aria-pressed','true')
    page.get_by_role('button',name='Remove filter: 2024',exact=True).click()
    expect(page.locator('.question-card')).to_have_count(2)
    page.locator('#search-input').fill('<script>not code</script>')
    expect(page.locator('.filter-token')).to_have_count(2)
    assert page.locator('#active-filters script').count()==0
    page.get_by_role('button',name='Remove filter: Search: <script>not code</script>',exact=True).click()
    page.get_by_role('button',name='Remove filter: Polity',exact=True).click()
    expect(page.locator('.question-card')).to_have_count(10)
    expect(page.locator('#study-view')).to_be_focused()
    note=page.locator('[data-action="toggle-note"]').first
    note.click();expect(note).to_have_attribute('aria-expanded','true')
    expect(page.locator('[data-note-id]').first).to_be_focused()
    page.locator('[data-note-id]').first.fill('A useful revision note.')
    note.click();expect(note).to_have_attribute('aria-expanded','false')
    expect(page.locator('.notes').first).to_be_hidden()
    page.locator('#notes-open').click()
    expect(page.locator('#notes-reader')).to_contain_text('A useful revision note.')
    page.locator('[data-close="notes-dialog"]').click()
    # Theme changes must reach the visible sidebar, its controls, and the mobile drawer.
    page.emulate_media(reduced_motion='reduce')
    themes = page.locator('#appearance-theme option').evaluate_all('(options)=>options.map(option=>option.value)')
    backgrounds = {}
    sidebar = page.locator('#question-sidebar')
    for width in [1440, 390]:
        page.set_viewport_size({'width':width, 'height':1000})
        for theme in themes:
            page.locator('.topbar .ai-settings-open').click()
            page.locator('#appearance-theme').select_option(theme)
            page.locator('#ai-settings-done').click()
            if not sidebar.is_visible():
                page.locator('#filters-toggle').click()
            expect(sidebar).to_be_visible()
            selected = page.locator('[data-year="2024"]')
            selected.click()
            page.locator('.sidebar-brand').hover()
            colors = sidebar.evaluate('''(sidebar) => {
                const style = getComputedStyle(sidebar);
                const input = sidebar.querySelector('input');
                const search = getComputedStyle(input);
                const active = getComputedStyle(sidebar.querySelector('button.active'));
                return {
                    text: [style.color, style.backgroundColor],
                    muted: [getComputedStyle(sidebar.querySelector('.filter-label')).color, style.backgroundColor],
                    search: [search.color, search.backgroundColor],
                    placeholder: [getComputedStyle(input, '::placeholder').color, search.backgroundColor],
                    selected: [active.color, active.backgroundColor]
                };
            }''')
            for label, pair in colors.items():
                assert contrast(*pair) >= 4.5, (theme, width, label, pair)
            selected.hover()
            assert selected.evaluate('(e)=>getComputedStyle(e).backgroundColor') == colors['selected'][1], (theme, 'selected hover')
            background = colors['text'][1]
            if width == 1440:
                backgrounds[theme] = background
            else:
                assert background == backgrounds[theme], (theme, 'mobile palette')
            page.locator('#reset-filters').click()
            page.reload()
            expect(page.locator('html')).to_have_attribute('data-theme', theme)
            if not sidebar.is_visible():
                page.locator('#filters-toggle').click()
            expect(sidebar).to_be_visible()
            assert sidebar.evaluate('(e)=>getComputedStyle(e).backgroundColor') == background, (theme, 'reload')
            if width == 390:
                page.locator('#sidebar-close').click()
    assert len(set(backgrounds.values())) == len(themes), backgrounds
    page.set_viewport_size({'width':1440, 'height':1000})
    # Existing user choices must survive the new defaults and a reload.
    page.locator('.topbar .ai-settings-open').click()
    page.locator('#appearance-theme').select_option('nord')
    page.locator('#text-style').select_option('sans')
    page.locator('#text-size').select_option('1.3')
    page.reload()
    expect(page.locator('html')).to_have_attribute('data-theme','nord')
    assert 'sans-serif' in page.locator('.question-stem').first.evaluate('(e)=>getComputedStyle(e).fontFamily')
    for width in [320,390,834,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
        page.locator('[data-action="explain"]').first.click()
        assert page.locator('#ai-dialog').evaluate('(e)=>e.scrollWidth <= e.clientWidth'),width
        page.locator('#ai-close').click()
    assert not errors,errors
    browser.close()
    print('PASS reading defaults, filter removal and escaping, note toggles/focus, notes library, all theme palettes and contrast on desktop/mobile, selected hover, retained appearance and large-text layouts')
