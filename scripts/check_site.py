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

# Installed before the libraries, also on reload. Measure the native sample
# handoff (smplr does not clamp past times), not just Tone callback punctuality.
PLAYBACK_PROBE = r"""(() => {
  const probe = window.playbackProbe = {starts: [], transportStarts: [], renders: [], turns: []};
  const sources = new WeakMap();
  const start = AudioBufferSourceNode.prototype.start;
  const stop = AudioBufferSourceNode.prototype.stop;
  AudioBufferSourceNode.prototype.start = function(when, ...args) {
    if (typeof when === 'number' && when > 0) {
      probe.context = this.context;
      const row = {when, ct: this.context.currentTime, t: performance.now(), stops: []};
      sources.set(this, row);
      probe.starts.push(row);
    }
    return start.call(this, when, ...args);
  };
  AudioBufferSourceNode.prototype.stop = function(when, ...args) {
    const row = sources.get(this);
    if (row) row.stops.push(when ?? this.context.currentTime);
    return stop.call(this, when, ...args);
  };
  let tone;
  Object.defineProperty(window, 'Tone', {configurable: true, get() { return tone; }, set(value) {
    tone = value;
    const transport = value.getTransport();
    // createPlayer calls Tone.setContext afterward, creating a new Transport
    // and bpm object. Patch prototypes so that native-context instance is seen.
    const prototype = Object.getPrototypeOf(transport);
    const start = prototype.start;
    prototype.start = function(...args) {
      probe.transportStarts.push({time: args[0] ?? this.context.now(), t: performance.now()});
      return start.apply(this, args);
    };
    const schedule = prototype.schedule;
    prototype.schedule = function(callback, ticks) {
      return schedule.call(this, time => {
        probe.callback = {time, ticks: parseInt(ticks, 10)};
        try { return callback(time); } finally { probe.callback = null; }
      }, ticks);
    };
    const bpmPrototype = Object.getPrototypeOf(transport.bpm);
    const setBpm = bpmPrototype.setValueAtTime;
    bpmPrototype.setValueAtTime = function(bpm, time, ...args) {
      const result = setBpm.call(this, bpm, time, ...args);
      if (probe.callback && bpm === probe.boundaryBpm) {
        probe.boundary = {...probe.callback, ct: probe.context.currentTime};
        // The observer runs after report() has updated scheduler-side activeTick,
        // but before the audio boundary. It must not depend on data-section now.
        document.getElementById('player').dataset.boundaryScheduled = String(time);
      }
      return result;
    };
  }});
})();"""

# Hook only after the wasm is ready, before a first visit to the tested pages.
RENDER_PROBE = """() => {
  const probe = window.playbackProbe;
  const original = verovio.toolkit.prototype.renderToSVG;
  verovio.toolkit.prototype.renderToSVG = function(page, ...args) {
    const start = performance.now();
    const svg = original.call(this, page, ...args);
    probe.renders.push({page, start, end: performance.now(), measure: document.getElementById('player').dataset.measure});
    return svg;
  };
  new MutationObserver(() => probe.turns.push({time: performance.now(),
    label: document.getElementById('page-label').textContent}))
    .observe(document.getElementById('page-label'), {childList:true, subtree:true, characterData:true});
}"""


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

    def data(name):
        return page.get_attribute('#player', 'data-' + name)

    def level(role, value):
        page.eval_on_selector(f'#parts-list input[type="range"][data-role="{role}"]',
                             "(e, v) => { e.value = v; e.dispatchEvent(new Event('input', {bubbles:true})); }", value)

    def guide_menu():
        page.eval_on_selector('.tempo-menu', 'e => { e.open = true; }')

    def section_field(n):
        return page.locator(f'#tempo-sections input[type="number"][aria-label^="m. {n} "]')

    def bpm(value):
        page.wait_for_function("b => +document.getElementById('player').dataset.bpm === b", arg=value, timeout=5000)

    def section(n, timeout=15000):
        page.wait_for_function("n => document.getElementById('player').dataset.section === n", arg=str(n), timeout=timeout)

    def parts_menu():
        page.eval_on_selector('.parts-menu', 'e => { e.open = true; }')

    def marks():
        page.wait_for_function("() => document.querySelectorAll('#score .is-playing').length > 0", timeout=2000)

    def wait_check(expression, description, timeout=5000, arg=None):
        try:
            page.wait_for_function(expression, arg=arg, timeout=timeout)
        except Exception as error:
            observed = page.evaluate("""() => ({state: document.getElementById('player').dataset.state,
              q: document.getElementById('player').dataset.position,
              page: document.getElementById('page-label').textContent,
              samples: playbackProbe.starts.length, renders: playbackProbe.renders})""")
            raise AssertionError(f'{description}: timed out after {timeout} ms; {observed}') from error

    page.set_viewport_size({'width': 1400, 'height': 1000})
    open_work('op1_01', 1)
    assert page.is_hidden('#player'), 'Playback must be off in a fresh context'
    page.evaluate("() => { document.activeElement.blur(); document.addEventListener('keydown', e => { if (e.code === 'Space') document.body.dataset.spacePrevented = String(e.defaultPrevented); }, {once:true}); }")
    page.keyboard.press('Space')
    assert page.get_attribute('body', 'data-space-prevented') == 'false'
    state('idle')
    # No stack or sample requests before the first Play (including phone/layout checks).
    lazy = page.evaluate(r"() => performance.getEntriesByType('resource').filter(e => /tone@|@tonejs\/midi@|smplr@|midi-js-soundfonts@|\/player.js/.test(e.name)).map(e => e.name)")
    assert not lazy, f'player fetched before Play: {lazy}'

    page.check('#playback')
    assert page.is_visible('#player')
    tempo(100)

    # The figured bass starts muted (the realization doubles it); the % boxes set the same values
    # as the sliders, on Enter, and clamp out-of-range input.
    parts_menu()
    assert not page.is_checked('#parts-list input[type="checkbox"][data-role="figured_continuo_bass"]')
    assert json.loads(data('muted')) == [2]
    assert 'doubles it' in page.inner_text('#bass-note')
    page.fill('#tempo-number', '80')
    page.press('#tempo-number', 'Enter')
    assert page.input_value('#tempo') == '80'
    page.fill('#tempo-number', '300')
    page.press('#tempo-number', 'Enter')
    assert page.input_value('#tempo') == '200' and page.input_value('#tempo-number') == '200'
    tempo(100)
    assert page.input_value('#tempo-number') == '100'
    volume_box = page.locator('#parts-list input[type="number"][data-role="violin"]')
    volume_box.fill('35')
    volume_box.press('Enter')
    assert json.loads(data('volumes'))['0'] == 35
    assert page.input_value('#parts-list input[type="range"][data-role="violin"]') == '35'
    level('violin', 100)
    assert volume_box.input_value() == '100'
    page.eval_on_selector('.parts-menu', 'e => { e.open = false; }')
    print('playback: figured bass muted by default; tempo and volume % boxes ok')

    # Playback off also cancels a first load. Release samples, observe idle,
    # then prove a fresh Play is usable. Reload gives the next cancellation
    # case a fresh player instance (routing disables the browser cache).
    off_pending = []
    def hold_off(route):
        off_pending.append(route)
        page.eval_on_selector('#player', "e => { e.dataset.offHeld = 'true'; }")
    page.route('**/midi-js-soundfonts@*/**', hold_off)
    page.click('#play')
    state('loading')
    page.wait_for_function("() => document.getElementById('player').dataset.offHeld === 'true'", timeout=60000)
    page.uncheck('#playback')
    state('idle')
    assert page.is_hidden('#player')
    for route in off_pending:
        route.continue_()
    page.unroute('**/midi-js-soundfonts@*/**', hold_off)
    page.wait_for_function(r"() => performance.getEntriesByType('resource').some(e => /midi-js-soundfonts@/.test(e.name) && e.responseEnd > 0)", timeout=60000)
    elapsed(snapshot(), 1000)
    state('idle')
    assert page.locator('.is-playing').count() == 0
    assert page.is_hidden('#player')
    page.check('#playback')
    page.click('#play')
    state('playing')
    assert data('work') == 'op1_01'
    page.click('#stop')
    page.reload()
    page.wait_for_selector('#score svg', timeout=60000)
    assert page.is_checked('#playback')
    open_work('op1_01', 1)
    print('playback: default off, Space untouched, off cancels sample load, re-enable plays')

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
    # C1: a steady first-page interval, after Play's separate pre-render task.
    elapsed(snapshot(), 500)
    page.evaluate('() => { playbackProbe.starts = []; }')
    elapsed(snapshot(), 3500)
    margins = sorted(page.evaluate('() => playbackProbe.starts.map(s => s.when - s.ct)'))
    assert len(margins) >= 10, f'C1 Op. I/1: only {len(margins)} sample starts in 3.5 s'
    p10 = margins[int((len(margins) - 1) * .1)]
    assert p10 >= .25, f'C1 Op. I/1: sample-start margin p10={p10*1000:.1f} ms, min={min(margins)*1000:.1f} ms, n={len(margins)}; need >=250 ms'
    print(f'playback C1: {len(margins)} sample starts, margin p10 {p10*1000:.1f} ms')
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

    # C3: choose a sample at least 50 ms in the future, avoiding a vacuous check
    # or a Playwright round trip consuming the old player's entire 25 ms horizon.
    for button, expected in [('#play', 'paused'), ('#stop', 'idle')]:
        wait_check('''() => {
          const now = playbackProbe.context.currentTime;
          const future = playbackProbe.starts.filter(s => s.when > now && !s.stops.some(w => w <= s.when));
          return future.length > 0 && future.every(s => s.when > now + .05);
        }''',
                   f'C3 {expected}: need a sample >50 ms ahead before halt')
        silence = page.evaluate("""button => {
          const p = playbackProbe, ct = p.context.currentTime;
          const future = p.starts.filter(s => s.when > ct);
          const pending = future.filter(s => !s.stops.some(w => w <= s.when)).length;
          document.querySelector(button).click();
          return {ct, returned: p.context.currentTime, count: p.starts.length, pending,
            future: future.map(s => ({when: s.when, stops: [...s.stops]}))};
        }""", button)
        state(expected)
        assert silence['pending'] > 0, f'C3 {expected}: no uncancelled future sample existed at halt, ct={silence["ct"]}'
        missed = [s for s in silence['future'] if not any(w <= s['when'] for w in s['stops'])]
        assert not missed, f'C3 {expected}: future sources lacked stop(w <= when) before return: {missed}; ct={silence["ct"]}, return={silence["returned"]}'
        elapsed(snapshot(), 500)
        count = page.evaluate('() => playbackProbe.starts.length')
        assert count == silence['count'], f'C3 {expected}: {count - silence["count"]} new sample starts within 0.5 s after halt'
        page.click('#play')
        state('playing')
    print('playback C3: Pause and Stop synchronously cancel future sources; no starts for 0.5 s')
    page.wait_for_function('() => +document.getElementById("player").dataset.position > .2', timeout=2000)

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
    assert float(page.get_attribute('#player', 'data-bpm')) == 51
    assert data('tempo-source') == 'guide'
    assert page.inner_text('#tempo-base') == '100 % = tempo guide'
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

    # Mute and level compose; All on must never rewrite the saved level.
    open_work('op1_01', 1)
    page.click('#play')
    state('playing')
    parts_menu()
    violin = page.locator('#parts-list input[type="checkbox"][data-role="violin"]')
    level('violin', 40)
    assert json.loads(data('gains'))['0'] == .4
    violin.uncheck()
    assert json.loads(data('gains'))['0'] == 0
    violin.check()
    assert json.loads(data('gains'))['0'] == .4
    level('violin', 0)
    violin.uncheck()
    violin.check()
    assert json.loads(data('gains'))['0'] == 0
    page.click('#all-parts')
    assert json.loads(data('gains'))['0'] == 0
    assert json.loads(data('volumes'))['0'] == 0
    level('figured_continuo_bass', 50)
    page.click('#stop')
    parts_menu()
    realization = page.locator('#parts-list input[type="checkbox"][data-role="keyboard_realization"]')
    realization.uncheck()
    assert json.loads(page.get_attribute('#player', 'data-muted')) == [3]
    tempo(75)
    page.reload()
    page.wait_for_selector('#score svg', timeout=60000)
    parts_menu()
    assert page.is_checked('#playback')
    assert json.loads(data('volumes'))['0'] == 0
    page.click('#play')
    state('playing')
    assert json.loads(data('gains'))['0'] == 0
    page.click('#stop')
    assert not realization.is_checked()
    assert json.loads(page.get_attribute('#player', 'data-muted')) == [3]
    assert page.input_value('#tempo') == '75'
    assert page.input_value('#tempo-number') == '75'
    tempo(100)
    open_work('app_02')
    assert json.loads(data('volumes'))['3'] == 50
    assert json.loads(data('volumes'))['2'] == 100
    page.click('#play')
    state('playing')
    assert json.loads(data('gains'))['3'] == .5
    assert json.loads(data('gains'))['2'] == 1
    page.click('#stop')
    assert json.loads(page.get_attribute('#player', 'data-muted')) == [4]
    assert not realization.is_checked()
    parts_menu()
    page.click('#all-parts')
    assert json.loads(page.get_attribute('#player', 'data-muted')) == []
    assert all(page.locator('#parts-list input[type="checkbox"]').nth(i).is_checked() for i in range(5))
    level('figured_continuo_bass', 100)
    open_work('op1_01', 1)
    parts_menu()
    level('violin', 100)
    print('playback: mute/volume independence, 0%, reload, role levels and All on ok')

    # Seek just before Lento, then cross the guide boundary without MIDI work.
    open_work('op1_01', 27)
    tempo(100)
    # C5: observe host notification time against the real scheduled audio time,
    # and the same frame's audible position (one tick plus an observed frame).
    page.evaluate("""() => {
      const probe = playbackProbe, p = document.getElementById('player');
      probe.boundaryBpm = 48;
      delete probe.boundary;
      let last = probe.context.currentTime, gap = 1 / 60;
      const frame = () => {
        const now = probe.context.currentTime;
        gap = now - last; last = now;
        if (!probe.notification) requestAnimationFrame(frame);
      };
      requestAnimationFrame(frame);
      const observer = new MutationObserver(() => {
        if (p.dataset.section !== '28' || !probe.boundary) return;
        probe.notification = {...probe.boundary, ct: probe.context.currentTime,
          q: +p.dataset.position, gap, scheduledCt: probe.boundary.ct};
        observer.disconnect();
      });
      observer.observe(p, {attributes:true, attributeFilter:['data-section']});
    }""")
    page.click('#play')
    state('playing')
    section(1)
    bpm(102)
    renders = snapshot()['renders']
    section(28)
    bpm(48)
    notification = page.evaluate('() => playbackProbe.notification')
    assert notification, 'C5 Op. I/1 m. 28: no scheduling/notification observation'
    ppq = page.evaluate('() => Tone.getTransport().PPQ')
    lag = notification['ct'] - notification['time']
    delta = notification['q'] - notification['ticks'] / ppq
    allowance = notification['gap'] + 60 / (48 * ppq)
    assert 0 <= lag <= allowance, f'C5 m. 28: host notification lag {lag*1000:.1f} ms; frame+tick allowance {allowance*1000:.1f} ms; {notification}'
    assert -1 / ppq <= delta <= 48 / 60 * allowance, f'C5 m. 28: host position differs from boundary by {delta:.4f} quarters; {notification}'
    assert snapshot()['renders'] == renders
    page.click('#stop')

    # Edit after the scheduling callback, before its audio time. data-section is
    # deliberately no longer the trigger: it now follows the audio itself.
    page.evaluate("""() => {
      const p = document.getElementById('player');
      delete p.dataset.boundaryScheduled;
      delete p.dataset.boundaryObserved;
      playbackProbe.notification = null;
      window.boundaryObserver = new MutationObserver(() => {
        if (!p.dataset.boundaryScheduled) return;
        window.boundaryObserver.disconnect();
        playbackProbe.edit = {...playbackProbe.boundary, ct: playbackProbe.context.currentTime};
        const slider = document.getElementById('tempo');
        slider.value = 50;
        slider.dispatchEvent(new Event('input', {bubbles:true}));
        p.dataset.boundaryObserved = 'true';
      });
      window.boundaryObserver.observe(p, {attributes:true, attributeFilter:['data-boundary-scheduled']});
    }""")
    page.click('#play')
    state('playing')
    page.wait_for_function("() => document.getElementById('player').dataset.boundaryObserved === 'true'", timeout=15000)
    section(28)
    bpm(24)
    edit = page.evaluate('() => playbackProbe.edit')
    assert edit['time'] - edit['ct'] >= .05, f'C5 live edit missed scheduling/audio window: only {(edit["time"]-edit["ct"])*1000:.1f} ms left; {edit}'
    page.wait_for_function('() => playbackProbe.context.currentTime > playbackProbe.edit.time + .1')
    assert float(data('bpm')) == 24, f'C5 stale boundary overwrote edited 24 bpm: {data("bpm")}'
    assert snapshot()['renders'] == renders
    guide_menu()
    field = section_field(28)
    field.fill('60')
    bpm(36)
    assert snapshot()['renders'] == renders
    page.click('#stop')
    page.reload()
    page.wait_for_selector('#score svg', timeout=60000)
    guide_menu()
    assert field.input_value() == '60'
    work = next(w for w in json.loads((SITE / 'works.json').read_text())['works'] if w['id'] == 'op1_01')
    for row in work['tempo']:
        assert section_field(row['n']).input_value() == str(60 if row['n'] == '28' else row['percent'])
    page.click('#copy-tempo')
    page.wait_for_function("() => document.getElementById('status').textContent.startsWith('Copied 1 changed sections in 1 works.')")
    copied = page.evaluate('navigator.clipboard.readText()')
    mid = next(r['measure'] for r in work['tempo'] if r['n'] == '28')
    assert copied.splitlines() == ['work_id,measure_n,measure_id,text,suggested_percent,your_percent', f'op1_01,28,{mid},Lento.,40,60']
    page.get_by_role('button', name='Reset m. 28 to 40 %', exact=True).click()
    assert field.input_value() == '40'
    assert page.evaluate("mid => !JSON.parse(localStorage.getItem('ddt-viewer-tempo-guide') || '{}').op1_01?.[mid]", mid)
    page.click('#copy-tempo')
    assert 'No changed sections to copy.' in page.inner_text('#status')
    tempo(100)
    open_work('op1_01', 29)
    page.click('#play')
    state('playing')
    section(28)
    bpm(48)
    page.click('#stop')
    print('playback: guide boundary, seek, lookahead edit, persistence, CSV Copy and Reset ok')

    open_work('app_02', 51)
    page.evaluate("""() => {
      const p = document.getElementById('player');
      let start = null;
      const observer = new MutationObserver(() => {
        if (p.dataset.state !== 'playing') return;
        if (start === null) start = +p.dataset.position;
        if (p.dataset.section === '51') {
          p.dataset.boundaryStart = start;
          p.dataset.boundaryPosition = p.dataset.position;
          observer.disconnect();
        }
      });
      observer.observe(p, {attributes:true, attributeFilter:['data-position', 'data-section']});
    }""")
    page.click('#play')
    state('playing')
    section(16)
    bpm(102)
    page.wait_for_function("() => document.getElementById('player').dataset.boundaryPosition !== undefined", timeout=15000)
    start, q = float(data('boundary-start')), float(data('boundary-position'))
    assert 2.9 <= q - start <= 3.3, (q, start)
    bpm(54)
    page.click('#stop')
    print('playback: App. II m. 51 changes at beat 4')

    open_work('app_01', 9)
    tempo(200)
    page.click('#play')
    state('playing')
    page.wait_for_function("() => document.getElementById('player-position').textContent.startsWith('m. 1 / ') && !!document.querySelector('#score .is-playing')", timeout=15000)
    assert page.evaluate('location.hash') == '#app_01/9'
    section(1)
    bpm(144)
    print('playback: App. I repeats to m. 1 with mapped second-pass notes')
    open_work('op1_02')
    state('idle')
    assert page.locator('.is-playing').count() == 0
    tempo(100)
    print('playback: work switch stops and clears every playing mark')

    # C4: preserve the real previous Transport history, including its old end.
    works = {w['id']: w for w in json.loads((SITE / 'works.json').read_text())['works']}
    root = ET.parse(SITE / works['op1_01']['mei']).getroot()
    last_n = root.findall(f'.//{MEI}music//{MEI}measure')[-1].get('n')
    open_work('op1_01', last_n)
    tempo(200)
    page.click('#play')
    state('playing')
    wait_check('() => document.getElementById("player").dataset.state === "idle"',
               f'C4 Op. I/1 last measure {last_n}: playback must reach end', timeout=45000)
    old_end = snapshot()['q']
    open_work('op1_01', 1)
    page.evaluate("""() => {
      const p = document.getElementById('player'), probe = playbackProbe;
      probe.restartPositions = [];
      window.restartObserver = new MutationObserver(() => {
        if (p.dataset.state !== 'playing') return;
        const transport = Tone.getTransport(), now = probe.context.currentTime;
        const start = probe.transportStarts.at(-1).time;
        probe.restartPositions.push({q: +p.dataset.position, beforeStart: now < start,
          audible: now < start ? 0 : transport.getTicksAtTime(now) / transport.PPQ});
      });
      window.restartObserver.observe(p, {attributes:true, attributeFilter:['data-position']});
    }""")
    page.click('#play')
    state('playing')
    restart_time = snapshot()['time']
    wait_check('t => performance.now() >= t + 1000 && document.getElementById("player").dataset.state === "playing"',
               'C4 Op. I/1 m. 1: must remain playing 1 s after restart', arg=restart_time)
    positions = page.evaluate('() => { restartObserver.disconnect(); return playbackProbe.restartPositions; }')
    assert positions and any(p['beforeStart'] for p in positions), f'C4: no observation before the new audio start: {positions}'
    wrong = [p for p in positions if p['q'] > p['audible'] + 1 / ppq + 1e-6 or (p['beforeStart'] and p['q'] != 0) or p['q'] >= old_end]
    assert not wrong, f'C4 restart from m. 1 exposed future/previous-run ticks (old end {old_end}): {wrong[:5]}'
    page.click('#stop')
    tempo(100)
    print(f'playback C4: reached end, restarted m. 1; {len(positions)} audible position observations, old end {old_end}')

    def go_page(number):
        while True:
            current_page = int(page.inner_text('#page-label').split('(')[1].split('/')[0])
            if current_page == number:
                return
            page.click('#next' if current_page < number else '#prev')

    def follow_to(number):
        wait_check('n => document.getElementById("page-label").textContent.includes("(" + n + "/")',
                   f'C2/C6 Op. I/4: expected follow turn to page {number}', arg=number, timeout=45000)

    def fresh_turn_work():
        # Earlier whole-site checks visited every page. Reload discards SVG/model
        # caches, so this really is a first-visit follow turn (Op. I/4 p. 8 -> 9).
        open_work('op1_04')
        page.reload()
        page.wait_for_selector('#score svg', timeout=60000)
        page.evaluate(RENDER_PROBE)
        go_page(8)
        page.locator('#score g.measure').last.dispatch_event('click')

    fresh_turn_work()
    page.evaluate('() => { playbackProbe.starts = []; playbackProbe.renders = []; playbackProbe.turns = []; }')
    page.click('#play')
    state('playing')
    # C6: Play pre-renders page 9, separate from Play's task, before its turn.
    wait_check('() => playbackProbe.renders.some(r => r.page === 9)', 'C6 Play: page 9 must be pre-rendered within 2 s', timeout=2000)
    play_render = page.evaluate('() => playbackProbe.renders.find(r => r.page === 9)')
    play_time = page.evaluate('() => playbackProbe.transportStarts.at(-1).t')
    assert play_render['start'] >= play_time + 49, f'C6 Play pre-render ran without 50 ms separation: {play_render}, Play at {play_time}'
    assert play_render['measure'] == '126', f'C6 Play: page 9 rendered at its follow turn instead of during m. 126: {play_render}'
    follow_to(9)
    turn = page.evaluate('() => playbackProbe.turns.find(t => t.label.includes("(9/"))')
    assert play_render['end'] <= turn['time'], f'C6 p. 9 rendered at turn instead of in advance: {play_render}, {turn}'
    wait_check('() => playbackProbe.renders.some(r => r.page === 10)', 'C6 follow to page 9: page 10 must be pre-rendered within 2 s', timeout=2000)
    next_render = page.evaluate('() => playbackProbe.renders.find(r => r.page === 10)')
    assert next_render['start'] >= turn['time'] + 49, f'C6 p. 10 pre-render joined follow turn task: {next_render}, {turn}'
    assert next_render['end'] <= turn['time'] + 2000, f'C6 p. 10 not cached within 2 s: {next_render}, {turn}'
    elapsed(snapshot(), 1000)
    starts = page.evaluate('t => playbackProbe.starts.filter(s => Math.abs(s.t - t) < 1000)', turn['time'])
    assert starts, 'C2 Op. I/4 p. 8 -> 9: no sample starts around first-visit follow turn'
    late = [s for s in starts if s['ct'] - s['when'] > .005]
    assert not late, f'C2 Op. I/4 p. 8 -> 9: {len(late)}/{len(starts)} sample starts >5 ms late; worst {max(s["ct"]-s["when"] for s in starts)*1000:.1f} ms'
    print(f'playback C2: first-visit Op. I/4 p. 8 -> 9, {len(starts)} starts, none >5 ms late')

    # The next actual follow turn must use that cached SVG, with zero toolkit
    # renders between Play and the turn; page 11's later idle job is separate.
    page.locator('#score g.measure').last.dispatch_event('click')
    second_play = page.evaluate('() => performance.now()')
    page.click('#play')
    state('playing')
    follow_to(10)
    next_turn = page.evaluate('() => playbackProbe.turns.find(t => t.label.includes("(10/"))')
    turn_renders = page.evaluate('v => playbackProbe.renders.filter(r => r.start >= v.start && r.start <= v.end)', {'start': second_play, 'end': next_turn['time']})
    assert not turn_renders, f'C6 cached follow p. 9 -> 10 called renderToSVG: {turn_renders}'
    page.click('#stop')

    # C2 positive control through the same native hook and the real player.
    open_work('op1_01', 1)
    page.click('#play')
    state('playing')
    elapsed(snapshot(), 1500)
    block = page.evaluate('''() => {
      playbackProbe.starts = [];
      const t = performance.now();
      while (performance.now() - t < 1000) {}
      return t;
    }''')
    elapsed(snapshot(), 1000)
    control = page.evaluate('t => playbackProbe.starts.filter(s => s.t >= t && s.t < t + 2000)', block)
    worst = max((s['ct'] - s['when'] for s in control), default=0)
    assert worst > .05, f'C2 positive control: 1 s busy loop produced no start >50 ms late; n={len(control)}, worst={worst*1000:.1f} ms'
    page.click('#stop')
    print(f'playback C2 control: 1 s block, worst sample start {worst*1000:.1f} ms late')

    # C6 guard: start a work switch in the turn's observer, before the 50 ms
    # delay. Hold getModel's fetch while current() is still the old model.
    fresh_turn_work()
    switching = []
    def hold_work(route):
        switching.append(route)
    page.route('**/' + works['op1_01']['mei'], hold_work)
    page.evaluate("""() => {
      const observer = new MutationObserver(() => {
        if (!document.getElementById('page-label').textContent.includes('(9/')) return;
        observer.disconnect();
        playbackProbe.switchAt = performance.now();
        location.hash = '#op1_01';
      });
      observer.observe(document.getElementById('page-label'), {childList:true});
    }""")
    page.click('#play')
    # The switch can already be idle by the time Playwright regains control.
    wait_check('() => playbackProbe.switchAt !== undefined', 'C6 guard: switch must start at follow to page 9', timeout=45000)
    wait_check('() => document.getElementById("play").disabled', 'C6 guard: work switch must enter loading')
    page.wait_for_timeout(300)  # exercise the deferred job during the held await
    assert switching, 'C6 work-switch guard: getModel fetch was not held'
    during_load = page.evaluate('() => playbackProbe.renders.filter(r => r.start >= playbackProbe.switchAt)')
    assert not during_load, f'C6 work-switch guard rendered while getModel awaited: {during_load}'
    for route in switching:
        route.continue_()
    page.unroute('**/' + works['op1_01']['mei'], hold_work)
    open_work('op1_01')

    def own_measures(work_id, number):
        expected, current_page = set(), 0
        for element in ET.parse(SITE / works[work_id]['mei']).getroot().find(f'{MEI}music').iter():
            if element.tag == MEI + 'pb':
                # Encoded first pb starts page 1.
                current_page += 1
            elif element.tag == MEI + 'measure' and max(current_page, 1) == number:
                expected.add(element.get('{http://www.w3.org/XML/1998/namespace}id'))
        actual = set(page.eval_on_selector_all('#score g.measure', 'els => els.map(e => e.id)'))
        assert actual == expected, f'C6 {work_id} page {number}: foreign/missing SVG measures; extra={sorted(actual-expected)}, missing={sorted(expected-actual)}'

    for work_id in ('op1_01', 'op1_04'):
        open_work(work_id)
        go_page(10)
        own_measures(work_id, 10)
    print('playback C6: Play/turn pre-render after 50 ms, next follow cached, work-switch await guarded; both works retain own measures')

    page.set_viewport_size({'width': 390, 'height': 844})
    parts_menu()
    page.wait_for_function('() => document.documentElement.scrollWidth <= innerWidth', timeout=5000)
    open_work('op1_06')
    guide_menu()
    page.wait_for_function('() => document.documentElement.scrollWidth <= innerWidth', timeout=5000)
    assert page.locator('#tempo-sections .tempo-row').count() == 11
    page.set_viewport_size({'width': 1400, 'height': 1000})
    page.evaluate('scrollTo(0, 0)')
    guide_menu()
    page.wait_for_function("() => document.querySelector('.tempo-panel').getBoundingClientRect().bottom <= innerHeight", timeout=5000)
    print('playback: Parts and 11-row guide fit 390px; desktop guide ends inside viewport')


def main():
    server = None if os.environ.get('SITE_URL') else serve()
    base = os.environ.get('SITE_URL') or f'http://127.0.0.1:{server.server_address[1]}/'
    works = json.loads((SITE / 'works.json').read_text())['works']
    problems, console = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1400, 'height': 1000}, permissions=['clipboard-read', 'clipboard-write'])
        context.add_init_script(PLAYBACK_PROBE)
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
