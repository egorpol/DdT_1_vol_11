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
