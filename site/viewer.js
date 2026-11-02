// Buxtehude, DdT 1, vol. 11 viewer: each work's MEI rendered by Verovio with
// the encoded page and system breaks (one rendered page per printed DdT page),
// the editorial notes with their source excerpts, and the BSB facsimile page
// from its IIIF server with the measure zones from the MEI. Ported from the
// webern_op27 viewer; works.json is written by scripts/build_site.py.
// Playback check contract on #player: data-state (idle/loading/playing/paused/error),
// data-position (audible quarter notes at AudioContext.currentTime; stored on pause/stop), data-bpm (effective), data-muted
// (JSON channel array from saved roles and DEFAULT_OFF), data-midi-renders (this visit),
// data-measure (notated @n), data-follow, and data-work (loaded work id).
// Also data-section (guide row @n, else ''), data-tempo-source (guide/single/midi),
// data-volumes (JSON channel: percent), data-gains (JSON last channel gains, {} before Play),
// data-sounds (JSON channel: sample GM program in use, {} before first Play),
// data-sound-loading (JSON channels with an authorized sound load in progress).
import { mapTempoSections } from './tempo-map.js';
import { SOUND_CHOICES, ENCODED_SOUNDS, soundKey, soundProgram, needsConsent, restoredChoice, allSound } from './sound-choice.js';

const VEROVIO_URL = 'https://cdn.jsdelivr.net/npm/verovio@6.3.0/dist/verovio-toolkit-wasm.js';
const VEROVIO_SRI = 'sha384-7oICD/hf52uWdE8X0lMFqe7iIspaUj3aQjeZUnBQZpxjrZcHtqlRd3C78cje2e19';
const REPO_BLOB = 'https://github.com/egorpol/DdT_1_vol_11/blob/main/';
// Relative refs in the notes resolve against the scores' folder in the repository.
const MEI_DIR = '11_buxtehude_sonatas_final/';
const EXCERPT_RIGHTS = `${REPO_BLOB}supplemental_material/README.md`;
// Printed DdT page p is BSB image p + 10.
const PAGE_OFFSET = 10;
const VEROVIO_OPTIONS = {
  breaks: 'encoded', adjustPageHeight: true, footer: 'none', svgViewBox: true, condense: 'none',
  scale: 35, spacingLinear: 0.25, spacingNonLinear: 0.6, minLastJustification: 0,
};
const SETTINGS = { playback: 'ddt-viewer-playback', markNotes: 'ddt-viewer-mark-notes', measureBoxes: 'ddt-viewer-measure-boxes' };
// The status line's opening text, shown again when a pin is dropped.
const STATUS_HINT = document.getElementById('status').textContent;
const XML_NS = 'http://www.w3.org/XML/1998/namespace';
const SVG_NS = 'http://www.w3.org/2000/svg';

const $ = (id) => document.getElementById(id);
const xmlId = (el) => el.getAttributeNS(XML_NS, 'id');
const refs = (value) => (value || '').split(/\s+/).filter(Boolean).map((v) => v.replace(/^#/, ''));
const squash = (text) => text.replace(/\s+/g, ' ').trim();

const state = { work: null, model: null, page: 1, pinned: null, annot: null };
const settings = { playback: false, markNotes: false, measureBoxes: false };
const models = new Map();
const fetchJson = (path) => fetch(path).then((r) => {
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
});
const indexReady = fetchJson('works.json');
const excerptsReady = fetchJson('supplemental_material/manifest.json');
let index = null;
let toolkit = null;
let workToken = 0;
let facsToken = 0;

// ---------------------------------------------------------------- loading

function loadVerovio() {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = VEROVIO_URL;
    script.integrity = VEROVIO_SRI;
    script.crossOrigin = 'anonymous';
    // The load event fires right after the script ran, before the wasm is ready.
    script.onload = () => {
      verovio.module.onRuntimeInitialized = () => {
        // Layout warnings ("justification is highly compressed") are of no use to a reader.
        verovio.enableLog(verovio.LOG_ERROR);
        resolve(new verovio.toolkit());
      };
    };
    script.onerror = () => reject(new Error('Verovio could not be loaded from jsDelivr.'));
    document.head.append(script);
  });
}

function getModel(work) {
  if (!models.has(work.id)) {
    models.set(work.id, Promise.all([fetch(work.mei), excerptsReady]).then(async ([response, excerpts]) => {
      if (!response.ok) throw new Error(`${work.mei}: HTTP ${response.status}`);
      return readModel(work, await response.text(), excerpts.items.filter((item) => item.work_key === work.key));
    }).catch((error) => {
      models.delete(work.id);
      throw error;
    }));
  }
  return models.get(work.id);
}

function enclosingMeasure(el) {
  for (let node = el; node; node = node.parentElement) {
    if (node.localName === 'measure') return xmlId(node);
  }
  return null;
}

function readModel(work, text, excerpts) {
  const doc = new DOMParser().parseFromString(text, 'application/xml');
  if (doc.getElementsByTagName('parsererror').length) throw new Error(`${work.label}: the MEI is not well-formed.`);
  const model = {
    work, ids: new Map(), measures: new Map(), byN: new Map(), pages: [], surfaces: new Map(), zones: new Map(),
    annots: [], noted: new Set(), excerpts: new Map(), loose: [], sources: new Map(), svg: new Map(), pageCount: 0,
  };
  const edition = doc.querySelector('editionStmt > edition');
  const version = edition?.getAttribute('n');
  model.edition = edition ? squash(edition.textContent) + (version ? `, version ${version}` : '') : '';
  for (const source of doc.querySelectorAll('sourceDesc > source')) {
    const title = source.getElementsByTagName('title')[0];
    if (title) model.sources.set(xmlId(source), squash(title.textContent));
  }

  for (const surface of doc.getElementsByTagName('surface')) {
    const graphic = surface.getElementsByTagName('graphic')[0];
    const target = graphic.getAttribute('target');
    const image = /_(\d{5})\/full\//.exec(target)?.[1];
    const sized = /\/full\/[^/]+\/0\/default\.jpg$/;
    model.surfaces.set(xmlId(surface), {
      id: xmlId(surface),
      target,
      iiif: sized.test(target) ? target.replace(sized, '') : null,
      image,
      printed: image ? String(Number(image) - PAGE_OFFSET) : surface.getAttribute('n'),
      width: Number(graphic.getAttribute('width')),
      height: Number(graphic.getAttribute('height')),
    });
    for (const zone of surface.getElementsByTagName('zone')) {
      const [ulx, uly, lrx, lry] = ['ulx', 'uly', 'lrx', 'lry'].map((a) => Number(zone.getAttribute(a)));
      model.zones.set(xmlId(zone), { surface: xmlId(surface), x: ulx, y: uly, w: lrx - ulx, h: lry - uly, measure: null });
    }
  }

  const annots = [];
  for (const el of doc.getElementsByTagName('music')[0].getElementsByTagName('*')) {
    const id = xmlId(el);
    if (el.localName === 'pb') model.pages.push({ n: el.getAttribute('n'), surface: refs(el.getAttribute('facs'))[0] });
    if (el.localName === 'measure') {
      const n = el.getAttribute('n');
      const zone = refs(el.getAttribute('facs'))[0];
      model.measures.set(id, { id, n, zone, page: Math.max(model.pages.length, 1) });
      model.byN.set(n, id);
      if (model.zones.has(zone)) model.zones.get(zone).measure = id;
    }
    if (el.localName === 'annot') annots.push(el);
    if (id) model.ids.set(id, { name: el.localName, measure: enclosingMeasure(el), end: refs(el.getAttribute('endid'))[0] });
  }
  model.annots = annots.map((el) => {
    const id = xmlId(el);
    const targets = refs(el.getAttribute('plist'));
    // A tie or slur among the targets also brings in the measure it ends in.
    const reached = [id, ...targets].flatMap((t) => [t, model.ids.get(t)?.end]);
    const bars = [...new Set(reached.map((t) => model.ids.get(t)?.measure).filter(Boolean))]
      .map((m) => model.measures.get(m))
      .sort((a, b) => Number(a.n) - Number(b.n));
    bars.forEach((bar) => model.noted.add(bar.id));
    const items = excerpts.filter((item) => item.annotation_id === id);
    return { id, label: el.getAttribute('label') || el.getAttribute('type'), targets, bars, paras: [...el.getElementsByTagName('p')], excerpts: items };
  });

  // Excerpts by measure, for the markers on the score. An excerpt whose note is
  // not in this file is listed on its own under "Source excerpts".
  for (const item of excerpts) {
    const measure = model.byN.get(String(item.measure));
    if (!measure) continue;
    const annot = model.annots.find((a) => a.id === item.annotation_id);
    if (!model.excerpts.has(measure)) model.excerpts.set(measure, { annot: annot?.id ?? null });
    if (!annot) model.loose.push({ ...item, measureId: measure });
  }

  model.text = new XMLSerializer().serializeToString(doc);
  return model;
}

// ---------------------------------------------------------------- score

const current = () => state.model;

function scoreMessage(text) {
  const p = document.createElement('p');
  p.className = 'message';
  p.textContent = text;
  $('score').replaceChildren(p);
}

function setStatus(text, id = '') {
  const code = document.createElement('code');
  code.textContent = id;
  $('status').replaceChildren(id ? `${text} · ` : text, code);
}

function link(text, href) {
  const a = document.createElement('a');
  a.href = href;
  a.textContent = text;
  return a;
}

function showWorkInfo(work, model) {
  $('work-title').textContent = `${work.label}: ${work.title}`;
  const status = document.createElement('span');
  status.className = `status status-${work.status}`;
  status.textContent = work.status;
  const parts = [`${work.catalogue} · DdT pp. ${work.pages.from}–${work.pages.to} · `, status];
  if (model) {
    parts.push(` · ${model.measures.size} measures · `, link('MEI', REPO_BLOB + work.source), ' · ', link('consistency report', REPO_BLOB + work.report));
  } else {
    parts.push(' · not yet assembled');
  }
  $('work-meta').replaceChildren(...parts);
  $('edition').textContent = model?.edition || '';
  document.title = `${work.label} · Buxtehude Instrumental Works`;
}

async function showWork(id) {
  // A new request, even for the work on show, outdates a load still running.
  const token = ++workToken;
  $('work').value = id;
  if (state.work?.id === id) {
    // Returning to the displayed work also cancels an intervening work load.
    if (playback.loadingWork) {
      playback.loadingWork = false;
      playerState('idle');
      showPage(state.page);
    }
    return;
  }
  stopPlayback(true);
  playback.loadingWork = true;
  playerState('idle');
  const work = index.works.find((w) => w.id === id);
  if (!work.mei) {
    Object.assign(state, { work, model: null, page: 1, pinned: null, annot: null });
    showWorkInfo(work, null);
    scoreMessage(`${work.label} (${work.catalogue}, DdT pp. ${work.pages.from}–${work.pages.to}) has not been assembled yet.`);
    renderNotes(null);
    $('page-label').textContent = '–';
    $('prev').disabled = true;
    $('next').disabled = true;
    renderParts(work);
    renderTempoGuide(work);
    playback.loadingWork = false;
    playerState('idle');
    renderFacsimile();
    return;
  }
  scoreMessage(`Loading ${work.label}…`);
  const model = await getModel(work);
  if (token !== workToken) return;
  if (!toolkit.loadData(model.text)) throw new Error(`Verovio could not load ${work.label}.`);
  model.pageCount = toolkit.getPageCount();
  Object.assign(state, { work, model, pinned: null, annot: null });
  playback.loadingWork = false;
  Object.assign($('player').dataset, { work: work.id });
  renderParts(work);
  renderTempoGuide(work);
  playerState('idle');
  showWorkInfo(work, model);
  renderNotes(model);
  showPage(1);
}

function showPage(page) {
  const model = current();
  if (!model) return;
  page = Math.min(Math.max(page, 1), model.pageCount);
  if (!model.svg.has(page)) model.svg.set(page, toolkit.renderToSVG(page));
  $('score').innerHTML = model.svg.get(page);
  state.page = page;
  decorate();
  const surface = model.surfaces.get(model.pages[page - 1]?.surface);
  $('page-label').textContent = `${surface ? `DdT p. ${surface.printed}` : 'page'} (${page}/${model.pageCount})`;
  $('prev').disabled = page <= 1;
  $('next').disabled = page >= model.pageCount;
  applyHighlights();
  applyPlaying();
  renderFacsimile();
}

let nextPageJob = null;
function preRenderNextPage() {
  // One job at a time, replacing an obsolete target after another turn/Play.
  if (nextPageJob) {
    clearTimeout(nextPageJob.delay);
    if (nextPageJob.idle !== undefined) {
      if (window.cancelIdleCallback) window.cancelIdleCallback(nextPageJob.idle);
      else clearTimeout(nextPageJob.idle);
    }
  }
  const model = current(), page = state.page + 1;
  nextPageJob = null;
  if (!model || page > model.pageCount || model.svg.has(page)) return;
  const job = {};
  nextPageJob = job;
  const render = () => {
    if (nextPageJob !== job) return;
    nextPageJob = null;
    // getModel awaits while current() can still be the old model. The loading
    // guard also covers that interval: the toolkit holds just one work's data.
    if (model === current() && !playback.loadingWork && !model.svg.has(page)) {
      model.svg.set(page, toolkit.renderToSVG(page));
    }
  };
  // Let Tone refill its horizon for two update intervals before another block.
  // This task renders only SVG; insertion/decoration wait for the actual turn.
  job.delay = setTimeout(() => {
    job.idle = window.requestIdleCallback ? window.requestIdleCallback(render) : setTimeout(render, 0);
  }, 50);
}

function svgElement(name, attributes = {}) {
  const el = document.createElementNS(SVG_NS, name);
  Object.entries(attributes).forEach(([k, v]) => el.setAttribute(k, v));
  return el;
}

// The distance between two staff lines, in the rendered page's units.
function staffSpace(measure) {
  const lines = [...measure.querySelectorAll(':scope > g.staff > path')].slice(0, 2).map((p) => p.getBBox().y);
  return lines.length === 2 && lines[1] > lines[0] ? lines[1] - lines[0] : 180;
}

// A box behind every rendered measure (shown by the settings) and a marker
// above each measure that has a source excerpt. An empty text, such as the one
// Verovio writes for a blank figure (<f/>), draws nothing, but Chrome counts it
// as a point at (0, 0) in getBBox and stretches the box to the page corner;
// hide it first.
function decorate() {
  const model = current();
  for (const text of $('score').querySelectorAll('g.measure text')) {
    if (!text.textContent.trim()) text.setAttribute('display', 'none');
  }
  for (const g of $('score').querySelectorAll('g.measure')) {
    if (!model.measures.has(g.id)) continue;
    const box = g.getBBox();
    const rect = svgElement('rect', { x: box.x, y: box.y, width: box.width, height: box.height, class: 'measure-box' });
    if (model.noted.has(g.id)) rect.classList.add('has-note');
    g.prepend(rect);
    if (model.excerpts.has(g.id)) g.append(excerptMarker(g.id, box, staffSpace(g)));
  }
}

function excerptMarker(measureId, box, u) {
  const size = 2.6 * u;
  const marker = svgElement('g', {
    class: 'excerpt-marker',
    'data-excerpt': measureId,
    transform: `translate(${box.x + box.width - size - u / 2} ${box.y - size - u / 2})`,
  });
  const title = svgElement('title');
  title.textContent = 'Source excerpt: show it with its note';
  marker.append(
    title,
    svgElement('rect', { class: 'frame', x: 0, y: 0, width: size, height: size, rx: u / 2 }),
    svgElement('path', { class: 'icon', d: `M ${0.45 * u} ${size - 0.5 * u} L ${size * 0.42} ${size * 0.42} L ${size * 0.62} ${size * 0.66} L ${size * 0.75} ${size * 0.52} L ${size - 0.45 * u} ${size - 0.5 * u} Z` }),
    svgElement('circle', { class: 'icon', cx: size * 0.7, cy: size * 0.28, r: u * 0.32 }),
  );
  return marker;
}

// Every rendered fragment of an element: the element itself and the
// continuations Verovio draws after a system break (class "id-<xml:id>").
function svgNodes(id) {
  return $('score').querySelectorAll(`[id="${CSS.escape(id)}"], .id-${CSS.escape(id)}`);
}

function applyHighlights() {
  const model = current();
  document.querySelectorAll('.is-pinned, .is-annot, .is-noted').forEach((n) => n.classList.remove('is-pinned', 'is-annot', 'is-noted'));
  if (!model) return;
  if (state.pinned) svgNodes(state.pinned).forEach((n) => n.classList.add('is-pinned'));
  if (settings.markNotes) model.annots.forEach((a) => a.targets.forEach((t) => svgNodes(t).forEach((n) => n.classList.add('is-noted'))));
  const annot = state.annot && model.annots.find((a) => a.id === state.annot);
  annot?.targets.forEach((t) => svgNodes(t).forEach((n) => n.classList.add('is-annot')));
  for (const rect of $('zones').children) rect.classList.toggle('is-pinned', rect.dataset.measure === state.pinned);
  document.querySelectorAll('.notes li > button[data-annot]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.annot === state.annot)));
}

function applySettings() {
  for (const el of [$('score'), document.querySelector('.facs-page')]) {
    el.classList.toggle('mark-notes', settings.markNotes);
    el.classList.toggle('show-boxes', settings.measureBoxes);
  }
  $('player').hidden = !settings.playback;
  applyHighlights();
}

function pin(measureId, { hash = true } = {}) {
  const model = current();
  const measure = model.measures.get(measureId);
  if (!measure) return;
  stopFollowing();
  state.pinned = measureId;
  if (hash) history.replaceState(null, '', `#${model.work.id}/${measure.n}`);
  if (measure.page !== state.page) showPage(measure.page);
  else applyHighlights();
  setStatus(`${model.work.label}, measure ${measure.n}`, measureId);
}

// Hover colours one element in the score (a note, or the measure from a zone)
// and outlines its measure's zone on the facsimile.
function hover(id, measureId) {
  document.querySelectorAll('.is-hover').forEach((n) => n.classList.remove('is-hover'));
  if (id) svgNodes(id).forEach((n) => n.classList.add('is-hover'));
  for (const rect of $('zones').children) rect.classList.toggle('is-hover', Boolean(measureId) && rect.dataset.measure === measureId);
}

// The nearest rendered ancestor that carries an xml:id from the MEI.
function sourceElement(target) {
  const model = current();
  for (let node = target; node && node !== $('score'); node = node.parentElement) {
    if (model.ids.has(node.id)) return node.id;
    const token = [...node.classList].find((c) => c.startsWith('id-') && model.ids.has(c.slice(3)));
    if (token) return token.slice(3);
  }
  return null;
}

function inspect(target) {
  const model = current();
  const id = model && sourceElement(target);
  if (!id) { hover(null); return; }
  const info = model.ids.get(id);
  const measure = model.measures.get(info.measure);
  hover(id, info.measure);
  setStatus(measure ? `Measure ${measure.n}, ${info.name}` : info.name, id);
}

// ---------------------------------------------------------------- playback
const SOUNDFONT_ROOT = 'https://cdn.jsdelivr.net/gh/gleitz/midi-js-soundfonts@044fab8e1456bfafc5776e86dfd6bb8697149aef/FluidR3_GM/';
const SAMPLE_FILES = {
  0: { url: `${SOUNDFONT_ROOT}acoustic_grand_piano-mp3.js`, integrity: 'sha384-Oe49rvfDnHMSSNlo8V6a4XyotASwNvpbHFgo0IOcyk8OFIXv8byikUYK2I3ONEfa' },
  19: { url: `${SOUNDFONT_ROOT}church_organ-mp3.js`, integrity: 'sha384-LvJh5PDp5xpmywJhQLNl67qLQfnjZf/qWPqWvyA7+KQFiLmdPUbaHDw5bSFtLYfN' },
  48: { url: `${SOUNDFONT_ROOT}string_ensemble_1-mp3.js`, integrity: 'sha384-gyGKjZg7zK8jqU1HhewujLPlSkilkeNxF080JTNSmBVy9Zn5vQwnFesUWv6WqF0u' },
  40: { url: `${SOUNDFONT_ROOT}violin-mp3.js`, integrity: 'sha384-HyplkbAwAFLDlT6JMUuvjLlS55QiD6H8Cx3A/KrGeJSUGQv62GCS5w7ML+bxsZkB' },
  42: { url: `${SOUNDFONT_ROOT}cello-mp3.js`, integrity: 'sha384-s/2S7jd5HFpdYzig+9zoDGj/JG4Beh0iT/QCHsp5MpTJqZTyd6dkDb4/Se1QmaRh' },
  43: { url: `${SOUNDFONT_ROOT}contrabass-mp3.js`, integrity: 'sha384-FH2/7J+D4GP4PFf//V3xIswsrDkclg1glB2nz9p4p37kXcXj7gL+6Hdvmrkl/8+J' },
  6: { url: `${SOUNDFONT_ROOT}harpsichord-mp3.js`, integrity: 'sha384-veZb4kehrh8qKJzOhM1Lv+MqBFb4SDXpSyWrnlNzeNwmz8RS8RI9iG8ysX221GgO' },
};
const PLAYBACK_SETTINGS = { tempo: 'ddt-viewer-tempo', parts: 'ddt-viewer-parts', volumes: 'ddt-viewer-volumes', guide: 'ddt-viewer-tempo-guide', sounds: 'ddt-viewer-sounds', consent: 'ddt-viewer-sound-consent' };
// Roles that start muted until the reader ticks them: Stiehl's realization doubles the figured
// bass (97-99.8 % of its notes at the same onset and pitch in each of the 17 works).
const DEFAULT_OFF = new Set(['figured_continuo_bass']);
const playback = {
  engine: null, ready: null, context: null, token: 0, state: 'idle', loadingWork: true,
  percent: 100, roles: {}, volumes: {}, guide: {}, engineModel: null, renders: 0, q: 0, start: null, pinAtPlay: null,
  sounds: {}, agreed: new Set(), consentStored: true, soundWork: null, accepted: {}, inUse: {}, pendingSounds: [],
  soundJobs: new Map(), soundVersions: new Map(),
  follow: false, active: new Set(), event: 0, measure: null,
};

function readPlaybackSettings() {
  try {
    const percent = Number(localStorage.getItem(PLAYBACK_SETTINGS.tempo));
    if (percent >= 25 && percent <= 200) playback.percent = percent;
    const roles = JSON.parse(localStorage.getItem(PLAYBACK_SETTINGS.parts) || '{}');
    if (roles && typeof roles === 'object' && !Array.isArray(roles)) playback.roles = roles;
  } catch { /* storage blocked: defaults */ }
  for (const key of ['volumes', 'guide', 'sounds']) {
    try {
      const value = JSON.parse(localStorage.getItem(PLAYBACK_SETTINGS[key]) || '{}');
      if (value && typeof value === 'object' && !Array.isArray(value)) playback[key] = value;
    } catch { /* storage blocked or malformed: defaults */ }
  }
  try {
    const files = JSON.parse(localStorage.getItem(PLAYBACK_SETTINGS.consent) || '[]');
    if (Array.isArray(files)) playback.agreed = new Set(files.filter((file) => typeof file === 'string'));
    // Probe writes too: some browsers permit reads but block persistence.
    localStorage.setItem(PLAYBACK_SETTINGS.consent, JSON.stringify([...playback.agreed]));
  } catch { playback.consentStored = false; }
  $('tempo').value = playback.percent;
  updateTempo();
}

function partOn(role) {
  return Object.hasOwn(playback.roles, role) ? playback.roles[role] !== false : !DEFAULT_OFF.has(role);
}

function mutedChannels() {
  return (state.work?.parts || []).filter((p) => !partOn(p.role)).map((p) => p.channel);
}

function updateMute() {
  const channels = mutedChannels();
  $('player').dataset.muted = JSON.stringify(channels);
  if (playback.engineModel === current()) { playback.engine?.setMuted(channels); showGains(); }
}

function initSounds(work) {
  if (playback.soundWork === work) return;
  playback.soundWork = work;
  playback.pendingSounds = [];
  playback.accepted = {};
  playback.inUse = {};
  playback.soundJobs.clear();
  playback.soundVersions.clear();
  for (const part of work?.parts || []) {
    const choice = restoredChoice(work.parts, part, playback.sounds, playback.agreed);
    playback.accepted[part.role] = choice.playable;
    if (choice.pending) playback.pendingSounds.push({ parts: [part], key: choice.key, all: false });
  }
  $('player').dataset.sounds = '{}';
}

function showSounds() {
  if (playback.engineModel === current() && playback.engine) {
    $('player').dataset.sounds = JSON.stringify(playback.engine.sounds);
  }
  $('player').dataset.soundLoading = JSON.stringify([...playback.soundJobs.keys()]);
  const actual = JSON.parse($('player').dataset.sounds);
  const changed = (state.work?.parts || []).some((p) =>
    (actual[p.channel] ?? soundProgram(p, playback.accepted[p.role])) !== p.program);
  document.querySelector('.parts-menu summary').textContent = changed ? 'Parts (sounds changed)' : 'Parts';
  renderSoundControls();
}

function removePending(parts) {
  const roles = new Set(parts.map((p) => p.role));
  for (const group of playback.pendingSounds) group.parts = group.parts.filter((p) => !roles.has(p.role));
  playback.pendingSounds = playback.pendingSounds.filter((group) => group.parts.length);
}

function chooseSound(parts, key, all = false) {
  removePending(parts);
  for (const part of parts) playback.sounds[part.role] = key;
  if (parts.some((p) => needsConsent(state.work.parts, p, key, playback.agreed))) {
    playback.pendingSounds.push({ parts, key, all });
  } else commitSound(parts, key);
  savePlayback('sounds');
  showSounds();
}

function commitSound(parts, key) {
  for (const part of parts) {
    playback.accepted[part.role] = key;
    swapSound(part, key);
  }
}

async function swapSound(part, key) {
  // Before Play (or after Stop), the next prepare consumes the authorized choices.
  if (!['playing', 'paused'].includes(playback.state) || playback.engineModel !== current()) return;
  const model = current(), token = playback.token;
  const version = (playback.soundVersions.get(part.role) || 0) + 1;
  playback.soundVersions.set(part.role, version);
  const program = soundProgram(part, key);
  const previous = playback.inUse[part.role] || 'encoded';
  playback.soundJobs.set(part.channel, version);
  showSounds();
  const valid = () => token === playback.token && model === current() && playback.soundVersions.get(part.role) === version;
  try {
    const applied = await playback.engine.setSound(part.channel, program);
    if (applied && valid()) playback.inUse[part.role] = key;
  } catch (error) {
    if (!valid()) return;
    playback.accepted[part.role] = previous;
    // A consent prompt opened while this load ran remains a separate choice.
    if (!playback.pendingSounds.some((group) => group.parts.includes(part))) playback.sounds[part.role] = previous;
    savePlayback('sounds');
    setStatus(`${SOUND_CHOICES[key]?.label || 'Encoded sound'} could not be loaded: ${error.message}`);
  } finally {
    if (valid()) { playback.soundJobs.delete(part.channel); showSounds(); }
  }
}

function renderSoundControls() {
  const parts = state.work?.parts || [];
  for (const host of document.querySelectorAll('#parts-list .sound-control')) {
    const all = host.dataset.role === 'all';
    const part = parts.find((p) => p.role === host.dataset.role);
    if (!all && !part) continue;
    let select = host.querySelector('select');
    if (!select) {
      select = document.createElement('select');
      select.dataset.role = host.dataset.role;
      select.setAttribute('aria-label', all ? 'All parts, sound' : `${part.label}, sound`);
      const encoded = all ? 'Encoded' : `Encoded (${ENCODED_SOUNDS[part.program]?.label || part.program})`;
      for (const [key, label] of [['mixed', 'Mixed'], ['encoded', encoded], ...Object.entries(SOUND_CHOICES).map(([k, v]) => [k, v.label])]) {
        const option = document.createElement('option');
        Object.assign(option, { value: key, textContent: label, disabled: key === 'mixed', hidden: key === 'mixed' && !all });
        select.append(option);
      }
      select.addEventListener('change', () => chooseSound(all ? parts : [part], select.value, all));
      const label = document.createElement('label');
      label.append(all ? 'All parts ' : 'Sound ', select);
      host.append(label);
    }
    // Keep controls/focus stable when another channel finishes loading.
    select.disabled = !parts.length;
    select.value = all ? allSound(parts, playback.sounds) : soundKey(playback.sounds[part.role]);
    const loading = host.querySelector('.sound-loading');
    if (all ? playback.soundJobs.size : playback.soundJobs.has(part.channel)) {
      if (!loading) {
        const span = document.createElement('span');
        span.className = 'sound-loading';
        span.textContent = 'Loading…';
        span.setAttribute('role', 'status');
        host.append(span);
      }
    } else loading?.remove();
    const group = playback.pendingSounds.find((g) => all ? g.all : !g.all && g.parts.includes(part));
    const previous = host.querySelector('.sound-consent');
    if (!group) { previous?.remove(); continue; }
    if (previous?.soundGroup === group && previous.dataset.remembered === String(playback.consentStored)) continue;
    previous?.remove();
    const choice = SOUND_CHOICES[group.key];
    const line = document.createElement('div');
    line.className = 'sound-consent';
    line.soundGroup = group;
    line.dataset.remembered = playback.consentStored;
    line.setAttribute('role', 'status');
    line.append(`${choice.label} needs a ${choice.mb} MB download from jsDelivr.`);
    if (!playback.consentStored) line.append(' Your browser will not remember this choice.');
    const allow = document.createElement('button'), cancel = document.createElement('button');
    Object.assign(allow, { type: 'button', textContent: 'Allow download' });
    Object.assign(cancel, { type: 'button', textContent: 'Cancel' });
    allow.addEventListener('click', () => {
      playback.agreed.add(choice.file);
      try { localStorage.setItem(PLAYBACK_SETTINGS.consent, JSON.stringify([...playback.agreed])); }
      catch { playback.consentStored = false; }
      // One agreement covers every pending choice for this file, including
      // several restored rows. Each group still carries its own selected key.
      const groups = playback.pendingSounds.filter((g) => SOUND_CHOICES[g.key].file === choice.file);
      for (const pending of groups) {
        const parts = [...pending.parts];
        removePending(parts);
        commitSound(parts, pending.key);
      }
      savePlayback('sounds');
      showSounds();
    });
    cancel.addEventListener('click', () => {
      for (const p of group.parts) playback.sounds[p.role] = playback.accepted[p.role];
      removePending([...group.parts]);
      savePlayback('sounds');
      showSounds();
    });
    line.append(' ', allow, ' ', cancel);
    host.append(line);
  }
}

function renderParts(work) {
  initSounds(work);
  const all = document.createElement('div');
  all.className = 'sound-control all-sound';
  all.dataset.role = 'all';
  $('parts-list').replaceChildren(all, ...(work?.parts || []).map((part) => {
    const label = document.createElement('label');
    const input = document.createElement('input');
    Object.assign(input, { type: 'checkbox', checked: partOn(part.role) });
    input.dataset.role = part.role;
    input.addEventListener('change', () => {
      playback.roles[part.role] = input.checked;
      try { localStorage.setItem(PLAYBACK_SETTINGS.parts, JSON.stringify(playback.roles)); } catch { /* not remembered */ }
      updateMute();
    });
    label.append(input, ` ${part.label}`);
    const slider = document.createElement('input');
    Object.assign(slider, { type: 'range', min: 0, max: 100, step: 1, value: partVolume(part.role) });
    slider.dataset.role = part.role;
    slider.setAttribute('aria-label', `${part.label}, volume %`);
    const box = document.createElement('input');
    Object.assign(box, { type: 'number', min: 0, max: 100, step: 1, value: slider.value });
    box.dataset.role = part.role;
    box.setAttribute('aria-label', `${part.label}, volume % (type a value)`);
    function setLevel(v) {
      playback.volumes[part.role] = v;
      slider.value = box.value = v;
      savePlayback('volumes');
      updateVolumes();
    }
    slider.addEventListener('input', () => setLevel(Number(slider.value)));
    // Applied on Enter, leaving the box or the spin arrows, never half-typed ("5" on the way to "50").
    box.addEventListener('change', () => {
      const v = Math.round(Number(box.value));
      setLevel(box.value === '' || !Number.isFinite(v) ? partVolume(part.role) : Math.max(0, Math.min(100, v)));
    });
    const value = document.createElement('span');
    value.className = 'part-volume';
    value.append(box, ' %');
    const row = document.createElement('div');
    row.className = 'part-row';
    const sound = document.createElement('div');
    sound.className = 'sound-control';
    sound.dataset.role = part.role;
    row.append(label, slider, value, sound);
    return row;
  }));
  updateMute();
  updateVolumes();
  showSounds();
}

function savePlayback(key) {
  try { localStorage.setItem(PLAYBACK_SETTINGS[key], JSON.stringify(playback[key])); } catch { /* not remembered */ }
}

function partVolume(role) {
  const v = playback.volumes[role];
  return Number.isFinite(v) && v >= 0 && v <= 100 ? v : 100;
}

function showGains() {
  if (playback.engine) $('player').dataset.gains = JSON.stringify(playback.engine.gains);
}

function updateVolumes() {
  const volumes = Object.fromEntries((state.work?.parts || []).map((p) => [p.channel, partVolume(p.role)]));
  $('player').dataset.volumes = JSON.stringify(volumes);
  if (playback.engineModel === current()) {
    playback.engine?.setVolumes(Object.fromEntries(Object.entries(volumes).map(([c, v]) => [c, v / 100])));
    showGains();
  }
}

function guideValue(work, row) {
  const value = playback.guide[work.id]?.[row.measure];
  return Number.isInteger(value) && value >= 25 && value <= 200 ? value : row.percent;
}

function cleanGuide() {
  const cleaned = {};
  for (const work of index.works) for (const row of work.tempo || []) {
    const v = guideValue(work, row);
    if (v !== row.percent) (cleaned[work.id] ||= {})[row.measure] = v;
  }
  playback.guide = cleaned;
  savePlayback('guide');
}

function tempoSections(model) {
  return (model.tempoPoints || []).map((p) => ({ ...p, factor: guideValue(model.work, model.work.tempo[p.index]) / 100 }));
}

function showTempo({ bpm, source, index: i }) {
  const row = source === 'guide' ? state.work?.tempo?.[i] : null;
  for (const [key, value] of Object.entries({ bpm, tempoSource: source, section: row?.n || '' })) {
    if ($('player').dataset[key] !== String(value)) $('player').dataset[key] = value;
  }
}

function updateTempo() {
  const model = current(), bpm = model?.midi?.header.tempos[0]?.bpm;
  const source = model?.midi?.header.tempos.length > 1 ? 'midi' : state.work?.tempo?.length ? 'guide' : 'single';
  if (document.activeElement !== $('tempo-number')) $('tempo-number').value = playback.percent;
  $('tempo-base').textContent = source === 'guide' ? '100 % = tempo guide' : source === 'midi' || !bpm ? '100 % = encoded tempo' : `100 % = ♩ ${Number(bpm.toFixed(2))}`;
  $('guide-disabled').hidden = source !== 'midi';
  document.querySelectorAll('#tempo-sections input, #tempo-sections button').forEach((e) => { e.disabled = source === 'midi'; });
  if (model && playback.engineModel === model) playback.engine.setTempo(playback.percent);
  else showTempo({ bpm: bpm ? bpm * playback.percent / 100 * (source === 'guide' ? guideValue(state.work, state.work.tempo[0]) / 100 : 1) : '', source, index: source === 'guide' ? 0 : -1 });
}

function renderTempoGuide(work) {
  $('tempo-copy').hidden = true;
  $('tempo-sections').replaceChildren(...(work?.tempo || []).map((row) => {
    const line = document.createElement('div');
    line.className = 'tempo-row';
    const measure = document.createElement('span'), word = document.createElement('span');
    measure.textContent = `m. ${row.n}`;
    word.textContent = row.text;
    const number = document.createElement('input'), slider = document.createElement('input');
    for (const [input, type] of [[number, 'number'], [slider, 'range']]) {
      Object.assign(input, { type, min: 25, max: 200, step: 1, value: guideValue(work, row) });
      input.dataset.measure = row.measure;
      input.setAttribute('aria-label', `m. ${row.n} ${row.text}, %`);
    }
    const reset = document.createElement('button');
    reset.type = 'button';
    reset.textContent = '↺';
    reset.setAttribute('aria-label', `Reset m. ${row.n} to ${row.percent} %`);
    reset.hidden = guideValue(work, row) === row.percent;
    function change(value) {
      if (!Number.isInteger(value) || value < 25 || value > 200) return;
      number.value = slider.value = value;
      const changes = playback.guide[work.id] ||= {};
      if (value === row.percent) delete changes[row.measure];
      else changes[row.measure] = value;
      if (!Object.keys(changes).length) delete playback.guide[work.id];
      reset.hidden = value === row.percent;
      savePlayback('guide');
      if (current() && playback.engineModel === current()) playback.engine.setSections(tempoSections(current()));
      updateTempo();
    }
    number.addEventListener('input', () => { if (number.value !== '') change(Number(number.value)); });
    number.addEventListener('change', () => {
      const value = number.value === '' ? guideValue(work, row) : Number(number.value);
      change(Math.max(25, Math.min(200, Math.round(value))));
    });
    slider.addEventListener('input', () => change(Number(slider.value)));
    reset.addEventListener('click', () => change(row.percent));
    line.append(measure, word, number, slider, reset);
    return line;
  }));
  updateTempo();
}

async function copyTempoChanges() {
  const lines = [['work_id', 'measure_n', 'measure_id', 'text', 'suggested_percent', 'your_percent']];
  const works = new Set();
  for (const work of index.works) for (const row of work.tempo || []) {
    const value = guideValue(work, row);
    if (value === row.percent) continue;
    lines.push([work.id, row.n, row.measure, row.text, row.percent, value]);
    works.add(work.id);
  }
  if (lines.length === 1) { setStatus('No changed sections to copy.'); return; }
  const csv = lines.map((line) => line.map((v) => /[",\r\n]/.test(String(v)) ? `"${String(v).replaceAll('"', '""')}"` : v).join(',')).join('\n') + '\n';
  try {
    await navigator.clipboard.writeText(csv);
    $('tempo-copy').hidden = true;
    setStatus(`Copied ${lines.length - 1} changed sections in ${works.size} works.`);
  } catch {
    $('tempo-copy').value = csv;
    $('tempo-copy').hidden = false;
    setStatus('Clipboard unavailable. Copy the tempo changes from the read-only text field.');
  }
}

function playerState(value) {
  playback.state = value;
  $('player').dataset.state = value;
  $('play').textContent = value === 'loading' ? 'Loading…' : value === 'playing' ? 'Pause' : 'Play';
  $('play').disabled = playback.loadingWork || !current() || value === 'loading';
  $('stop').disabled = playback.loadingWork || !current() || value === 'idle';
}

function stopFollowing() {
  playback.follow = false;
  $('player').dataset.follow = 'false';
}

function clearPlaying() {
  for (const root of [$('score'), $('zones')]) {
    root.querySelectorAll('.is-playing').forEach((n) => n.classList.remove('is-playing'));
  }
}

function applyPlaying() {
  clearPlaying();
  if (playback.state !== 'playing') return;
  const model = current();
  for (const raw of playback.active) {
    const id = model.playingIds.get(raw);
    if (id) svgNodes(id).forEach((n) => n.classList.add('is-playing'));
  }
  for (const rect of $('zones').children) rect.classList.toggle('is-playing', rect.dataset.measure === playback.measure);
}

function showPosition(q, measureId = playback.measure) {
  playback.q = q;
  playback.measure = measureId;
  const measure = current()?.measures.get(measureId);
  Object.assign($('player').dataset, { position: q, measure: measure?.n || '' });
  const text = measure ? `m. ${measure.n} / ${current().measures.size}` : '–';
  if ($('player-position').textContent !== text) $('player-position').textContent = text;
}

function advanceCursor(q) {
  const model = current();
  if (!model?.playbackMap) return;
  let changed = false;
  while (playback.event < model.playbackMap.length && model.playbackMap[playback.event].qstamp <= q + 1 / model.midi.header.ppq + 1e-9) {
    const event = model.playbackMap[playback.event++];
    for (const id of event.off) playback.active.delete(id);
    for (const id of event.on) playback.active.add(id);
    if (event.measure) playback.measure = event.measure;
    changed = true;
  }
  showPosition(q);
  const measure = model.measures.get(playback.measure);
  if (playback.follow && measure && measure.page !== state.page) {
    showPage(measure.page);
    preRenderNextPage();
  } else if (changed) applyPlaying();
}

function resetCursor(q, measure) {
  clearPlaying();
  playback.active.clear();
  playback.event = 0;
  playback.measure = measure;
  advanceCursor(q);
}

function stopPlayback(workSwitch = false) {
  ++playback.token; // Pending imports/sample loads may finish, but cannot start.
  const start = !workSwitch && playback.start;
  playback.engine?.stop(start?.q || 0);
  playback.soundJobs.clear();
  // Keep decoded sounds: the next work's prepare reuses each channel whose sound is unchanged.
  if (workSwitch) { playback.engineModel = null; $('player').dataset.sounds = '{}'; }
  showSounds();
  stopFollowing();
  playerState('idle');
  clearPlaying();
  playback.active.clear();
  if (workSwitch) {
    playback.start = null;
    playback.pinAtPlay = null;
  }
  showPosition(start?.q || 0, start?.id || null);
  const measure = current()?.measures.get(start?.id);
  if (measure && measure.page !== state.page) showPage(measure.page);
  if (workSwitch) setStatus(STATUS_HINT);
  else if (measure) setStatus(`Stopped at m. ${measure.n}`);
}

async function getPlayer() {
  if (!playback.ready) {
    playback.ready = import('./player.js').then(({ createPlayer }) => createPlayer({
      context: playback.context, samples: SAMPLE_FILES,
      onTempo: (tempo) => { if (playback.engineModel === current()) showTempo(tempo); },
      onPosition: advanceCursor, onEnd: () => stopPlayback(),
    })).then((engine) => { playback.engine = engine; return engine; }).catch((error) => {
      playback.ready = null;
      throw error;
    });
  }
  return playback.ready;
}

function cachePlayback(model, engine) {
  if (model.midi && model.timemap) return;
  // This toolkit still holds model.text: work/token checked immediately before this call.
  model.midi = engine.parseMidi(toolkit.renderToMIDI());
  ++playback.renders;
  $('player').dataset.midiRenders = playback.renders;
  model.timemap = toolkit.renderToTimemap().sort((a, b) => a.qstamp - b.qstamp);
  model.playingIds = new Map();
  function notated(id) {
    if (!id) return null;
    if (model.playingIds.has(id)) return model.playingIds.get(id);
    const stripped = id.replace(/-rend\d+$/, '');
    const mapped = model.ids.has(id) ? id : model.ids.has(stripped) ? stripped : toolkit.getNotatedIdForElement(id);
    const result = model.ids.has(mapped) ? mapped : null;
    model.playingIds.set(id, result);
    return result;
  }
  model.playbackMap = model.timemap.map((event) => {
    const on = (event.on || []).filter((id) => notated(id));
    const off = (event.off || []).filter((id) => notated(id));
    return { qstamp: event.qstamp, on, off, measure: model.ids.get(notated(on[0] || ''))?.measure };
  });
  model.measureQ = new Map();
  for (const measure of model.measures.values()) {
    const ms = toolkit.getTimeForElement(measure.id);
    // Find by the measured millisecond time; never key or equate qstamp floats.
    let low = 0, high = model.timemap.length;
    while (low < high) {
      const mid = (low + high) >>> 1;
      if (model.timemap[mid].tstamp < ms) low = mid + 1;
      else high = mid;
    }
    let i = Math.min(low, model.timemap.length - 1);
    if (i > 0 && Math.abs(model.timemap[i - 1].tstamp - ms) < Math.abs(model.timemap[i].tstamp - ms)) --i;
    model.measureQ.set(measure.id, model.timemap[i].qstamp);
    model.playbackMap[i].measure = measure.id;
  }
  model.tempoPoints = mapTempoSections(model.work.tempo || [], [...model.measures.keys()], model.playbackMap, model.measureQ);
}

async function togglePlayback() {
  if (!settings.playback || !current() || playback.loadingWork || playback.state === 'loading') return;
  const newPin = state.pinned && state.pinned !== playback.pinAtPlay;
  if (playback.state === 'playing' && !newPin) {
    showPosition(playback.engine.pause());
    playerState('paused');
    clearPlaying();
    setStatus(`Paused at m. ${current().measures.get(playback.measure)?.n}`);
    return;
  }
  const model = current(), token = ++playback.token;
  const resume = playback.state === 'paused' && !newPin;
  // Before the first await: preserve the native user gesture on Safari as well.
  try {
    playback.context ||= new (window.AudioContext || window.webkitAudioContext)();
    const resumed = playback.context.resume();
    playback.engine?.stop();
    playerState('loading');
    clearPlaying();
    const [engine] = await Promise.all([getPlayer(), resumed]);
    if (token !== playback.token || model !== current()) return;
    cachePlayback(model, engine);
    updateTempo();
    let prepared;
    // Choices may change during first-Play downloads. Reconcile before starting;
    // pending consent always keeps the previous authorized (or encoded) program.
    while (true) {
      const parts = model.work.parts.map((p) => ({ ...p, sound: soundProgram(p, playback.accepted[p.role]) }));
      playback.soundJobs = new Map(parts.map((p) => [p.channel, 0]));
      showSounds();
      prepared = await engine.prepare(model.midi, parts);
      if (token !== playback.token || model !== current()) return;
      if (parts.every((p) => p.sound === soundProgram(p, playback.accepted[p.role]))) break;
    }
    playback.soundJobs.clear();
    if (token !== playback.token || model !== current()) return;
    const id = state.pinned || [...model.measures.values()].find((m) => m.page === state.page)?.id || model.measures.keys().next().value;
    const q = resume ? playback.q : model.measureQ.get(id) || 0;
    if (!resume) playback.start = { id, q };
    playback.pinAtPlay = state.pinned;
    playback.follow = true;
    $('player').dataset.follow = 'true';
    playerState('playing');
    resetCursor(q, resume ? playback.measure : id);
    playback.engineModel = model;
    engine.setSections(tempoSections(model));
    updateVolumes();
    engine.setMuted(mutedChannels());
    engine.play(prepared, q, playback.percent);
    playback.inUse = { ...playback.accepted };
    preRenderNextPage();
    showGains();
    showSounds();
    setStatus(`Playing from m. ${model.measures.get(playback.measure)?.n}`);
  } catch (error) {
    if (token !== playback.token || model !== current()) return;
    playback.engine?.stop();
    clearPlaying();
    playerState('error');
    playback.soundJobs.clear();
    showSounds();
    const reason = /[.!?]$/.test(error.message) ? error.message : `${error.message}.`;
    setStatus(`Playback could not start: ${reason} Press Play to retry.`);
  }
}

// ---------------------------------------------------------------- notes

function inlineText(node, parent, model) {
  for (const child of node.childNodes) {
    if (child.nodeType === Node.TEXT_NODE) parent.append(child.textContent.replace(/\s+/g, ' '));
    else if (child.localName === 'ref' && child.getAttribute('target')) {
      const target = child.getAttribute('target');
      let el;
      if (target.startsWith('#')) {
        // A source in the MEI header: name it on hover.
        el = document.createElement('span');
        el.className = 'ref';
        el.title = model.sources.get(target.slice(1)) || target.slice(1);
      } else {
        el = document.createElement('a');
        el.href = new URL(target, REPO_BLOB + MEI_DIR).href;
      }
      inlineText(child, el, model);
      parent.append(el);
    } else if (child.localName === 'lb') parent.append(document.createElement('br'));
    else if (child.nodeType === Node.ELEMENT_NODE) inlineText(child, parent, model);
  }
}

function excerptFigure(item) {
  const figure = document.createElement('figure');
  figure.className = 'excerpt';
  const image = document.createElement('img');
  Object.assign(image, { src: item.file, width: item.width, height: item.height, loading: 'lazy' });
  image.alt = `Source excerpt: ${item.instrument}, measure ${item.measure}`;
  const full = link('', item.file);
  full.append(image);
  const caption = document.createElement('figcaption');
  const rights = item.rights || {};
  caption.append(
    `${item.caption} `,
    document.createElement('br'),
    `${rights.intended_use || 'Image quotation'}${rights.jurisdiction_basis ? ` (${rights.jurisdiction_basis})` : ''}; not covered by the edition's licenses. `,
    link('Rights note', EXCERPT_RIGHTS),
  );
  figure.append(full, caption);
  return figure;
}

function noteHeading(where, labelText, data) {
  const button = document.createElement('button');
  button.type = 'button';
  Object.assign(button.dataset, data);
  const place = document.createElement('span');
  place.className = 'where';
  place.textContent = where;
  button.append(place);
  if (labelText) {
    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = labelText;
    button.append(label);
  }
  return button;
}

// "Measure 17", "Measures 16–17", "Measures 110, 148, 164"; a note spread over
// more than four runs gives its span and count.
function measuresLabel(bars) {
  const runs = [];
  for (const n of bars.map((bar) => Number(bar.n))) {
    const run = runs.at(-1);
    if (run && n === run[1] + 1) run[1] = n;
    else runs.push([n, n]);
  }
  if (bars.length === 1) return `Measure ${bars[0].n}`;
  if (runs.length > 4) return `Measures ${runs[0][0]}–${runs.at(-1)[1]} (${bars.length} measures)`;
  return `Measures ${runs.map(([a, b]) => (a === b ? a : `${a}–${b}`)).join(', ')}`;
}

function renderNotes(model) {
  const list = $('annots');
  list.replaceChildren();
  for (const annot of model?.annots || []) {
    const li = document.createElement('li');
    li.append(noteHeading(measuresLabel(annot.bars), annot.label.replace(/-/g, ' '), { annot: annot.id }));
    for (const para of annot.paras) {
      const p = document.createElement('p');
      inlineText(para, p, model);
      li.append(p);
    }
    if (annot.excerpts.length) {
      li.dataset.excerpts = annot.excerpts.map((item) => model.byN.get(String(item.measure))).join(' ');
      annot.excerpts.forEach((item) => li.append(excerptFigure(item)));
    }
    list.append(li);
  }
  $('notes-heading').textContent = `Editorial notes (${model?.annots.length ?? 0})`;

  // Excerpts without a note in this file, one entry per measure, partbooks stacked.
  const loose = $('excerpts');
  loose.replaceChildren();
  const byMeasure = Map.groupBy(model?.loose || [], (item) => item.measureId);
  for (const [measureId, items] of byMeasure) {
    const li = document.createElement('li');
    li.dataset.excerpts = measureId;
    li.append(noteHeading(`Measure ${model.measures.get(measureId).n}`, '', { measure: measureId }), ...items.map(excerptFigure));
    loose.append(li);
  }
  $('excerpts-section').hidden = !byMeasure.size;
}

function selectAnnot(id) {
  const annot = current().annots.find((a) => a.id === id);
  state.annot = state.annot === id ? null : id;
  if (state.annot && annot.bars.length) pin(annot.bars[0].id);
  else applyHighlights();
}

// From a marker on the score to the excerpt: its note is selected and scrolled into view.
function openExcerpt(measureId) {
  const entry = current().excerpts.get(measureId);
  if (entry.annot && state.annot !== entry.annot) selectAnnot(entry.annot);
  else if (!entry.annot) pin(measureId);
  document.querySelector(`.notes li[data-excerpts~="${CSS.escape(measureId)}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ---------------------------------------------------------------- facsimile

function showFacsError(text) {
  $('facs-error').textContent = text;
  $('facs-error').hidden = !text;
}

// The IIIF image is requested in steps of 500 pixels, no wider than the
// graphic the zones were measured on.
function imageWidth(surface) {
  const pixels = ($('facs').clientWidth || 600) * (window.devicePixelRatio || 1);
  return Math.min(surface.width, Math.ceil(pixels / 500) * 500);
}

const imageUrl = (surface, width) => (surface.iiif ? `${surface.iiif}/full/${width},/0/default.jpg` : surface.target);

function drawZones(model, surface) {
  const zones = $('zones');
  zones.setAttribute('viewBox', `0 0 ${surface.width} ${surface.height}`);
  zones.replaceChildren(...[...model.zones.values()]
    .filter((z) => z.surface === surface.id && z.measure)
    .map((z) => {
      const rect = svgElement('rect', { x: z.x, y: z.y, width: z.w, height: z.h });
      rect.dataset.measure = z.measure;
      if (model.noted.has(z.measure)) rect.classList.add('has-note');
      return rect;
    }));
  applyPlaying();
}

function renderFacsimile() {
  const model = current();
  const page = document.querySelector('.facs-page');
  const image = $('facs-image');
  const surface = model?.surfaces.get(model.pages[state.page - 1]?.surface);
  page.hidden = !surface;
  $('facs-full').hidden = !surface;
  if (!surface) {
    ++facsToken;
    $('facs-label').textContent = model ? '' : 'No facsimile: the work has not been assembled yet.';
    return;
  }
  const width = imageWidth(surface);
  const label = `DdT p. ${surface.printed} · BSB image ${surface.image}`;
  $('facs-full').href = surface.target;
  if (image.dataset.surface === surface.id && Number(image.dataset.width) >= width) {
    ++facsToken;
    page.classList.remove('is-loading');
    showFacsError('');
    $('facs-label').textContent = label;
    drawZones(model, surface);
    applyHighlights();
    return;
  }
  const token = ++facsToken;
  const src = imageUrl(surface, width);
  const next = new Image();
  next.src = src;
  page.classList.add('is-loading');
  $('facs-label').textContent = `${label} · loading…`;
  next.decode().then(() => {
    if (token !== facsToken) return;
    showFacsError('');
    page.style.aspectRatio = `${surface.width} / ${surface.height}`;
    image.src = src;
    image.alt = `DdT 1903, printed page ${surface.printed}`;
    Object.assign(image.dataset, { surface: surface.id, width });
    page.classList.remove('is-loading');
    $('facs-label').textContent = label;
    drawZones(model, surface);
    applyHighlights();
    // Fetch the next page ahead, at the same size.
    const following = model.surfaces.get(model.pages[state.page]?.surface);
    if (following) new Image().src = imageUrl(following, width);
  }).catch(() => {
    if (token !== facsToken) return;
    page.classList.remove('is-loading');
    image.removeAttribute('src');
    delete image.dataset.surface;
    $('zones').replaceChildren();
    $('facs-label').textContent = label;
    showFacsError(`The facsimile page could not be loaded from the BSB server: ${src}`);
  });
}

// ---------------------------------------------------------------- wiring

function fillWorkSelect() {
  const select = $('work');
  const groups = { op1: 'Op. I', op2: 'Op. II', app: 'Appendix' };
  select.replaceChildren(...Object.entries(groups).map(([prefix, name]) => {
    const group = document.createElement('optgroup');
    group.label = name;
    for (const work of index.works.filter((w) => w.id.split('_')[0] === prefix)) {
      const option = document.createElement('option');
      option.value = work.id;
      option.textContent = `${work.label}: ${work.title} (${work.catalogue})${work.mei ? '' : ' · pending'}`;
      group.append(option);
    }
    return group;
  }));
  select.disabled = false;
}

async function applyHash() {
  const match = /^#([a-z]+\d?_\d\d)(?:\/(\d+))?$/.exec(location.hash);
  const known = match && index.works.some((w) => w.id === match[1]);
  await showWork(known ? match[1] : state.work?.id || index.works.find((w) => w.mei).id);
  if (location.hash && !known) setStatus(`No work “${location.hash.slice(1)}” in this edition.`);
  if (!known || !current()) return;
  const n = match[2] === undefined ? null : String(Number(match[2]));
  const id = n && current().byN.get(n);
  if (id) { pin(id, { hash: false }); return; }
  // A link to the work alone, or to a measure it lacks, drops an earlier pin.
  if (state.pinned) {
    state.pinned = null;
    applyHighlights();
    setStatus(STATUS_HINT);
  }
  if (n) setStatus(`${state.work.label} has no measure ${n}.`);
}

function readSettings() {
  for (const [name, key] of Object.entries(SETTINGS)) {
    try { settings[name] = localStorage.getItem(key) === '1'; } catch { /* storage blocked: defaults */ }
  }
  $('playback').checked = settings.playback;
  $('mark-notes').checked = settings.markNotes;
  $('measure-boxes').checked = settings.measureBoxes;
}

function changeSetting(name, value) {
  settings[name] = value;
  if (name === 'playback' && !value) stopPlayback();
  try { localStorage.setItem(SETTINGS[name], value ? '1' : '0'); } catch { /* not remembered */ }
  applySettings();
}

function bindUi() {
  $('work').addEventListener('change', (e) => { location.hash = `#${e.target.value}`; });
  $('prev').addEventListener('click', () => { stopFollowing(); showPage(state.page - 1); });
  $('next').addEventListener('click', () => { stopFollowing(); showPage(state.page + 1); });
  $('play').addEventListener('click', togglePlayback);
  $('stop').addEventListener('click', () => stopPlayback());
  function setGlobalTempo(value) {
    playback.percent = value;
    $('tempo').value = $('tempo-number').value = value;
    updateTempo();
    try { localStorage.setItem(PLAYBACK_SETTINGS.tempo, playback.percent); } catch { /* not remembered */ }
  }
  $('tempo').addEventListener('input', (e) => setGlobalTempo(Number(e.target.value)));
  // Applied on Enter, leaving the box or the spin arrows; out-of-range values are clamped.
  $('tempo-number').addEventListener('change', (e) => {
    const v = Math.round(Number(e.target.value));
    setGlobalTempo(e.target.value === '' || !Number.isFinite(v) ? playback.percent : Math.max(25, Math.min(200, v)));
  });
  $('all-parts').addEventListener('click', () => {
    // Every part on, the figured bass too; levels stay as set.
    for (const part of state.work?.parts || []) playback.roles[part.role] = true;
    try { localStorage.setItem(PLAYBACK_SETTINGS.parts, JSON.stringify(playback.roles)); } catch { /* not remembered */ }
    renderParts(state.work);
  });
  $('copy-tempo').addEventListener('click', copyTempoChanges);
  $('playback').addEventListener('change', (e) => changeSetting('playback', e.target.checked));
  $('mark-notes').addEventListener('change', (e) => changeSetting('markNotes', e.target.checked));
  $('measure-boxes').addEventListener('change', (e) => changeSetting('measureBoxes', e.target.checked));
  document.addEventListener('keydown', (e) => {
    if (!current() || e.altKey || e.ctrlKey || e.metaKey || e.target.closest('input, select, textarea, [contenteditable]')) return;
    if (settings.playback && e.code === 'Space' && !e.target.closest('button, summary')) { e.preventDefault(); togglePlayback(); }
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
      stopFollowing();
      showPage(state.page + (e.key === 'ArrowLeft' ? -1 : 1));
    }
  });
  window.addEventListener('hashchange', () => applyHash().catch((e) => scoreMessage(e.message)));

  const score = $('score');
  score.addEventListener('mouseover', (e) => inspect(e.target));
  score.addEventListener('mouseleave', () => hover(null));
  score.addEventListener('click', (e) => {
    stopFollowing();
    const marker = e.target.closest('.excerpt-marker');
    if (marker) { openExcerpt(marker.dataset.excerpt); return; }
    const id = current() && sourceElement(e.target);
    const measure = id && current().ids.get(id).measure;
    if (measure) pin(measure);
  });

  for (const list of [$('annots'), $('excerpts')]) {
    list.addEventListener('click', (e) => {
      const button = e.target.closest('li > button');
      if (button?.dataset.annot) selectAnnot(button.dataset.annot);
      else if (button?.dataset.measure) pin(button.dataset.measure);
    });
  }

  const zones = $('zones');
  zones.addEventListener('mouseover', (e) => {
    const measure = current()?.measures.get(e.target.dataset?.measure);
    if (!measure) return;
    hover(measure.id, measure.id);
    setStatus(`Measure ${measure.n}, zone`, measure.zone);
  });
  zones.addEventListener('mouseleave', () => hover(null));
  zones.addEventListener('click', (e) => {
    stopFollowing();
    if (e.target.dataset?.measure) pin(e.target.dataset.measure);
  });

  let lastWidth = 0;
  new ResizeObserver(([entry]) => {
    const width = Math.round(entry.contentRect.width);
    if (width !== lastWidth) { lastWidth = width; renderFacsimile(); }
  }).observe($('facs'));
}

async function main() {
  readSettings();
  readPlaybackSettings();
  bindUi();
  applySettings();
  try {
    [index, toolkit] = await Promise.all([indexReady, loadVerovio()]);
    cleanGuide();
    toolkit.setOptions(VEROVIO_OPTIONS);
    $('verovio-version').textContent = toolkit.getVersion();
    fillWorkSelect();
    await applyHash();
  } catch (error) {
    scoreMessage(error.message);
  }
}

main();
