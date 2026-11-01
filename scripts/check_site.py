"""Headless check of the built viewer (_site): every page of every work.

Usage: python check_site.py SITE_DIR SHOT_DIR [work-id ...]
Set SITE_URL to check a deployed copy of SITE_DIR instead of serving it.
"""
import functools
import http.server
import json
import os
import sys
import threading
import xml.etree.ElementTree as ET
from pathlib import Path

from playwright.sync_api import sync_playwright

SITE = Path(sys.argv[1]).resolve()
SHOTS = Path(sys.argv[2]).resolve()
ONLY = set(sys.argv[3:])
MEI = '{http://www.music-encoding.org/ns/mei}'
# Measure boxes reaching far beyond their staves (an empty <text> once pulled
# them to the page corner): ids of the measures.
STRETCHED = """() => [...document.querySelectorAll('#score rect.measure-box')].filter(r => {
  const staves = [...r.parentElement.querySelectorAll(':scope > g.staff')].map(s => s.getBBox());
  if (!staves.length) return false;
  const top = Math.min(...staves.map(b => b.y)), bottom = Math.max(...staves.map(b => b.y + b.height));
  const left = Math.min(...staves.map(b => b.x)), right = Math.max(...staves.map(b => b.x + b.width));
  const x = +r.getAttribute('x'), y = +r.getAttribute('y'), w = +r.getAttribute('width'), h = +r.getAttribute('height');
  return Math.max(top - y, y + h - bottom, left - x, x + w - right) > 3000;
}).map(r => r.parentElement.id)"""


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    handler.log_message = lambda *a: None
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def mei_counts(path):
    root = ET.parse(path).getroot()
    return len(root.findall(f'.//{MEI}music//{MEI}measure')), len(root.findall(f'.//{MEI}zone'))


def check_playback(page):
    """Playback assertions use documented DOM state and the rendered score/zones."""
    def state(value, timeout=60000):
        page.wait_for_function("s => document.getElementById('player').dataset.state === s", arg=value, timeout=timeout)

    def open_work(work_id, measure=None):
        page.evaluate("h => { location.hash = h; }", '#' + work_id + (f'/{measure}' if measure else ''))
        page.wait_for_function("id => document.getElementById('player').dataset.work === id && !!document.querySelector('#score svg') && !document.getElementById('play').disabled", arg=work_id, timeout=60000)
        if measure:
            page.wait_for_function("n => location.hash.endsWith('/' + n) && !!document.querySelector('#score .is-pinned')", arg=str(measure))

    def snapshot():
        return page.eval_on_selector('#player', "e => ({q: +e.dataset.position, time: performance.now(), renders: +e.dataset.midiRenders, measure: e.dataset.measure})")

    def elapsed(start, ms):
        # Wait for DOM updates and elapsed observation time, without a fixed sleep.
        page.wait_for_function("v => performance.now() >= v.time + v.ms && document.getElementById('player').dataset.state === v.state", arg={'time': start['time'], 'ms': ms, 'state': page.get_attribute('#player', 'data-state')}, timeout=10000)
        return snapshot()

    def tempo(value):
        return page.eval_on_selector('#tempo', "(e, v) => { const p = document.getElementById('player'); const before = p.dataset.measure; e.value = v; e.dispatchEvent(new Event('input', {bubbles:true})); return [before, p.dataset.measure]; }", value)

    def parts_menu():
        page.eval_on_selector('.parts-menu', 'e => { e.open = true; }')

    def marks():
        page.wait_for_function("() => document.querySelectorAll('#score .is-playing').length > 0", timeout=2000)

    page.set_viewport_size({'width': 1400, 'height': 1000})
    open_work('op1_01', 1)
    tempo(100)
    # No stack or sample requests before the first Play (including phone/layout checks).
    lazy = page.evaluate(r"() => performance.getEntriesByType('resource').filter(e => /tone@|@tonejs\/midi@|smplr@|midi-js-soundfonts@|\/player.js/.test(e.name)).map(e => e.name)")
    assert not lazy, f'player fetched before Play: {lazy}'

    # Hold the first sample requests to exercise cancellation during loading.
    pending = []
    def hold_sample(route):
        pending.append(route)
        page.eval_on_selector('#player', "e => { e.dataset.sampleHeld = 'true'; }")
    page.route('**/midi-js-soundfonts@*/**', hold_sample)
    page.click('#play')
    state('loading')
    page.wait_for_function("() => document.getElementById('player').dataset.sampleHeld === 'true'", timeout=60000)
    assert pending, 'no sample request reached the first Play'
    open_work('op1_02')
    state('idle')
    # Release the held requests before unroute: unroute itself hands them on,
    # and a later continue_() then raises 'Route is already handled'.
    for route in pending:
        route.continue_()
    page.unroute('**/midi-js-soundfonts@*/**', hold_sample)
    page.click('#play')
    state('playing')
    marks()
    assert page.get_attribute('#player', 'data-work') == 'op1_02'
    page.click('#stop')
    state('idle')
    assert page.locator('.is-playing').count() == 0
    print('playback: work switch during sample load cancelled; next Play uses Op. I/2')

    open_work('op1_01', 1)
    cached_renders = snapshot()['renders']
    page.click('#play')
    state('playing')
    assert snapshot()['renders'] == cached_renders, 'returning to a work rendered MIDI again'
    first = snapshot()
    marks()
    page.wait_for_function('q => +document.getElementById("player").dataset.position > q + 0.2', arg=first['q'], timeout=2000)
    assert 'Playing from m. 1' in page.inner_text('#status')
    page.click('#play')
    state('paused')
    paused = snapshot()
    after = elapsed(paused, 500)
    assert after['q'] == paused['q'], (paused, after)
    page.click('#play')
    state('playing')
    page.wait_for_function('q => +document.getElementById("player").dataset.position > q + 0.2', arg=paused['q'], timeout=2000)
    page.focus('#tempo')
    page.keyboard.press('Space')
    assert page.get_attribute('#player', 'data-state') == 'playing'
    page.eval_on_selector('#tempo', 'e => e.blur()')
    page.keyboard.press('Space')
    state('paused')
    page.keyboard.press('Space')
    state('playing')
    print('playback: Play, marks, advancing ticks, Pause and resume ok')

    before = snapshot()
    normal = elapsed(before, 2000)
    same = tempo(50)
    assert same[0] == same[1], f'tempo moved measure: {same}'
    slow_start = snapshot()
    slow = elapsed(slow_start, 2000)
    normal_rate = (normal['q'] - before['q']) / (normal['time'] - before['time'])
    slow_rate = (slow['q'] - slow_start['q']) / (slow['time'] - slow_start['time'])
    assert 0.375 <= slow_rate / normal_rate <= 0.625, (normal_rate, slow_rate)
    assert slow['renders'] == before['renders']
    assert float(page.get_attribute('#player', 'data-bpm')) == 60
    assert page.inner_text('#tempo-base') == '100 % = ♩ 120'
    tempo(100)
    page.click('#stop')
    state('idle')
    print('playback: live tempo halves tick rate without moving measure or rendering MIDI')

    # Pin through the real score click handler, at the last measure of page 3.
    page.click('#next')
    page.click('#next')
    assert '(3/' in page.inner_text('#page-label')
    last = page.locator('#score g.measure').last
    pinned_id = last.get_attribute('id')
    last.dispatch_event('click')
    pinned_hash = page.evaluate('location.hash')
    pinned_n = pinned_hash.rsplit('/', 1)[1]
    page.click('#play')
    state('playing')
    assert page.inner_text('#player-position').startswith(f'm. {pinned_n} / ')
    page.wait_for_function("() => document.getElementById('page-label').textContent.includes('(4/') && !!document.querySelector('#score .is-playing')", timeout=45000)
    assert page.get_attribute('#player', 'data-measure') != pinned_n
    assert page.evaluate('location.hash') == pinned_hash
    page.wait_for_function("() => !!document.querySelector('#zones .is-playing') && !document.getElementById('facs-label').textContent.includes('loading')", timeout=60000)
    assert page.evaluate("() => [...document.querySelectorAll('.is-playing')].every(e => e.closest('#score, #zones'))")
    assert page.get_attribute('#player', 'data-follow') == 'true'
    # A manual turn suspends follow. Stop returns to the original pin.
    page.click('#prev')
    assert page.get_attribute('#player', 'data-follow') == 'false'
    page.click('#stop')
    state('idle')
    assert page.locator('.is-playing').count() == 0
    assert page.locator(f'#score [id="{pinned_id}"].is-pinned').count() == 1
    assert page.inner_text('#player-position').startswith(f'm. {pinned_n} / ')
    assert page.evaluate('location.hash') == pinned_hash
    print('playback: page 3 -> 4, score and scan marks, independent pin, manual turn and Stop ok')

    parts_menu()
    realization = page.locator('#parts-list input[data-role="keyboard_realization"]')
    realization.uncheck()
    assert json.loads(page.get_attribute('#player', 'data-muted')) == [3]
    tempo(75)
    page.reload()
    page.wait_for_selector('#score svg', timeout=60000)
    parts_menu()
    assert not realization.is_checked()
    assert json.loads(page.get_attribute('#player', 'data-muted')) == [3]
    assert page.input_value('#tempo') == '75'
    tempo(100)
    open_work('app_02')
    assert json.loads(page.get_attribute('#player', 'data-muted')) == [4]
    assert not realization.is_checked()
    parts_menu()
    page.click('#all-parts')
    assert json.loads(page.get_attribute('#player', 'data-muted')) == []
    assert all(page.locator('#parts-list input').nth(i).is_checked() for i in range(5))
    print('playback: role mute survives reload and maps realization 3 -> 4; All on ok')

    open_work('app_01', 9)
    tempo(200)
    page.click('#play')
    state('playing')
    page.wait_for_function("() => document.getElementById('player-position').textContent.startsWith('m. 1 / ') && !!document.querySelector('#score .is-playing')", timeout=15000)
    assert page.evaluate('location.hash') == '#app_01/9'
    print('playback: App. I repeats to m. 1 with mapped second-pass notes')
    open_work('op1_02')
    state('idle')
    assert page.locator('.is-playing').count() == 0
    tempo(100)
    print('playback: work switch stops and clears every playing mark')

    page.set_viewport_size({'width': 390, 'height': 844})
    parts_menu()
    page.wait_for_function('() => document.documentElement.scrollWidth <= innerWidth', timeout=5000)
    print('playback: phone controls and expanded Parts menu fit 390px')


def main():
    server = None if os.environ.get('SITE_URL') else serve()
    base = os.environ.get('SITE_URL') or f'http://127.0.0.1:{server.server_address[1]}/'
    works = json.loads((SITE / 'works.json').read_text())['works']
    problems, console = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1400, 'height': 1000})
        page = context.new_page()
        page.on('console', lambda m: m.type == 'error' and console.append(m.text))
        page.on('pageerror', lambda e: console.append(f'pageerror: {e}'))
        page.on('requestfailed', lambda r: console.append(f'requestfailed: {r.url} {r.failure}'))
        page.on('response', lambda r: r.status >= 400 and console.append(f'HTTP {r.status}: {r.url}'))
        page.goto(base)
        page.wait_for_selector('#score svg', timeout=60000)
        for work in works:
            if ONLY and work['id'] not in ONLY:
                continue
            page.evaluate("id => { location.hash = '#' + id; }", work['id'])
            if not work.get('mei'):
                page.wait_for_function("t => document.getElementById('work-title').textContent.includes(t)", arg=work['label'])
                msg = page.inner_text('#score')
                print(f"{work['id']}: pending -> {msg!r}")
                continue
            page.wait_for_function("t => document.getElementById('work-title').textContent.startsWith(t) && document.querySelector('#score svg')", arg=work['label'] + ':', timeout=60000)
            measures, zones = mei_counts(SITE / work['mei'])
            rendered, seen_pages = set(), 0
            while True:
                label = page.inner_text('#page-label')
                printed = label.split(' (')[0]
                page.wait_for_function(
                    "p => { const l = document.getElementById('facs-label').textContent; return (l.startsWith(p + ' ·') && !l.includes('loading')) || !document.getElementById('facs-error').hidden; }",
                    arg=printed, timeout=60000)
                if page.is_visible('#facs-error'):
                    problems.append(f"{work['id']} {printed}: {page.inner_text('#facs-error')}")
                ids = page.eval_on_selector_all('#score g.measure', 'els => els.map(e => e.id)')
                zone_ids = page.eval_on_selector_all('#zones rect', 'els => els.map(e => e.dataset.measure)')
                if sorted(ids) != sorted(zone_ids):
                    problems.append(f"{work['id']} {printed}: {len(ids)} measures rendered, {len(zone_ids)} zones")
                stretched = page.evaluate(STRETCHED)
                if stretched:
                    problems.append(f"{work['id']} {printed}: measure boxes beyond their staves: {', '.join(stretched)}")
                if page.evaluate("() => document.getElementById('facs-image').naturalWidth") == 0:
                    problems.append(f"{work['id']} {printed}: facsimile image empty")
                rendered.update(ids)
                seen_pages += 1
                if page.is_disabled('#next'):
                    break
                page.click('#next')
                page.wait_for_function("l => document.getElementById('page-label').textContent !== l", arg=label)
            ok = len(rendered) == measures == zones
            print(f"{work['id']}: {seen_pages} pages, {len(rendered)} measures rendered, MEI {measures} measures / {zones} zones {'ok' if ok else 'MISMATCH'}")
            if not ok:
                problems.append(f"{work['id']}: rendered {len(rendered)}, MEI {measures}/{zones}")
            notes = page.locator('#annots > li').count()
            figures = page.locator('.excerpt img')
            for i in range(figures.count()):
                figures.nth(i).scroll_into_view_if_needed()
                page.wait_for_function('img => img.complete && img.naturalWidth > 0', arg=figures.nth(i).element_handle(), timeout=20000)
            if figures.count():
                print(f"   {notes} notes, {figures.count()} excerpt image(s) loaded")

        if not ONLY or 'op2_02' in ONLY:
            # Excerpt marker -> note, settings, deep link.
            page.evaluate("() => { location.hash = '#op2_02/189'; }")
            page.wait_for_selector('.excerpt-marker', timeout=30000)
            page.click('.excerpt-marker')
            pressed = page.get_attribute('button[data-annot="editorial_y1dubf9q"]', 'aria-pressed')
            print('marker click selects the note:', pressed)
            if pressed != 'true':
                problems.append('marker click did not select editorial_y1dubf9q')
            page.check('#mark-notes')
            page.check('#measure-boxes')
            noted = page.locator('#score .is-noted').count()
            boxes = page.locator('#score rect.measure-box').count()
            zone_notes = page.locator('#zones rect.has-note').count()
            print(f'mark notes: {noted} highlighted nodes; boxes: {boxes}; noted zones: {zone_notes}')
            page.reload()
            page.wait_for_selector('#score svg', timeout=60000)
            kept = page.is_checked('#mark-notes') and page.is_checked('#measure-boxes')
            print('settings kept after reload:', kept)
            if not kept:
                problems.append('settings not remembered')
            page.set_viewport_size({'width': 1000, 'height': 900})
            page.evaluate("() => { location.hash = '#op2_02/199'; }")
            page.wait_for_function("() => document.getElementById('page-label').textContent.startsWith('DdT p. ') && !document.getElementById('facs-label').textContent.includes('loading')")
            page.wait_for_timeout(500)
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / 'viewer-1000.png'))
            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(300)
            overflow = page.evaluate('() => document.documentElement.scrollWidth - window.innerWidth')
            print('phone width horizontal overflow (px):', overflow)
            if overflow > 0:
                problems.append(f'horizontal overflow {overflow}px at 390px')
            page.screenshot(path=str(SHOTS / 'viewer-390.png'))
        try:
            check_playback(page)
        except Exception as error:
            problems.append(f'playback: {type(error).__name__}: {error}')
        browser.close()
    if server:
        server.shutdown()
    print('console errors:', len(console))
    for line in console[:20]:
        print('  ', line[:300])
    print('problems:', len(problems))
    for line in problems:
        print('  ', line)
    return 1 if problems or console else 0


if __name__ == '__main__':
    sys.exit(main())
