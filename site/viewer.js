// Buxtehude, DdT 1, vol. 11 viewer: each work's MEI rendered by Verovio with
// the encoded page and system breaks (one rendered page per printed DdT page),
// the editorial notes with their source excerpts, and the BSB facsimile page
// from its IIIF server with the measure zones from the MEI. Ported from the
// webern_op27 viewer; works.json is written by scripts/build_site.py.

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
const SETTINGS = { markNotes: 'ddt-viewer-mark-notes', measureBoxes: 'ddt-viewer-measure-boxes' };
// The status line's opening text, shown again when a pin is dropped.
const STATUS_HINT = document.getElementById('status').textContent;
const XML_NS = 'http://www.w3.org/XML/1998/namespace';
const SVG_NS = 'http://www.w3.org/2000/svg';

const $ = (id) => document.getElementById(id);
const xmlId = (el) => el.getAttributeNS(XML_NS, 'id');
const refs = (value) => (value || '').split(/\s+/).filter(Boolean).map((v) => v.replace(/^#/, ''));
const squash = (text) => text.replace(/\s+/g, ' ').trim();

const state = { work: null, model: null, page: 1, pinned: null, annot: null };
const settings = { markNotes: false, measureBoxes: false };
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
  model.edition = edition ? `${squash(edition.textContent)}, version ${edition.getAttribute('n')}` : '';
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

  // Verovio builds the page header from meiHead but leaves a composer encoded as
  // composer/persName blank (Verovio #4512); give it the name as plain text.
  for (const composer of doc.querySelectorAll('meiHead composer')) {
    if (composer.getElementsByTagName('persName').length) composer.textContent = squash(composer.textContent);
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
  if (state.work?.id === id) return;
  const work = index.works.find((w) => w.id === id);
  if (!work.mei) {
    Object.assign(state, { work, model: null, page: 1, pinned: null, annot: null });
    showWorkInfo(work, null);
    scoreMessage(`${work.label} (${work.catalogue}, DdT pp. ${work.pages.from}–${work.pages.to}) has not been assembled yet.`);
    renderNotes(null);
    $('page-label').textContent = '–';
    $('prev').disabled = true;
    $('next').disabled = true;
    renderFacsimile();
    return;
  }
  scoreMessage(`Loading ${work.label}…`);
  const model = await getModel(work);
  if (token !== workToken) return;
  if (!toolkit.loadData(model.text)) throw new Error(`Verovio could not load ${work.label}.`);
  model.pageCount = toolkit.getPageCount();
  Object.assign(state, { work, model, pinned: null, annot: null });
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
  renderFacsimile();
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
  applyHighlights();
}

function pin(measureId, { hash = true } = {}) {
  const model = current();
  const measure = model.measures.get(measureId);
  if (!measure) return;
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
    `${rights.intended_use || 'Image quotation'}${rights.jurisdiction_basis ? ` (${rights.jurisdiction_basis})` : ''}; not covered by the MIT License. `,
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
  $('mark-notes').checked = settings.markNotes;
  $('measure-boxes').checked = settings.measureBoxes;
}

function changeSetting(name, value) {
  settings[name] = value;
  try { localStorage.setItem(SETTINGS[name], value ? '1' : '0'); } catch { /* not remembered */ }
  applySettings();
}

function bindUi() {
  $('work').addEventListener('change', (e) => { location.hash = `#${e.target.value}`; });
  $('prev').addEventListener('click', () => showPage(state.page - 1));
  $('next').addEventListener('click', () => showPage(state.page + 1));
  $('mark-notes').addEventListener('change', (e) => changeSetting('markNotes', e.target.checked));
  $('measure-boxes').addEventListener('change', (e) => changeSetting('measureBoxes', e.target.checked));
  document.addEventListener('keydown', (e) => {
    if (!current() || e.altKey || e.ctrlKey || e.metaKey || e.target.closest('input, select, textarea')) return;
    if (e.key === 'ArrowLeft') showPage(state.page - 1);
    if (e.key === 'ArrowRight') showPage(state.page + 1);
  });
  window.addEventListener('hashchange', () => applyHash().catch((e) => scoreMessage(e.message)));

  const score = $('score');
  score.addEventListener('mouseover', (e) => inspect(e.target));
  score.addEventListener('mouseleave', () => hover(null));
  score.addEventListener('click', (e) => {
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
  zones.addEventListener('click', (e) => { if (e.target.dataset?.measure) pin(e.target.dataset.measure); });

  let lastWidth = 0;
  new ResizeObserver(([entry]) => {
    const width = Math.round(entry.contentRect.width);
    if (width !== lastWidth) { lastWidth = width; renderFacsimile(); }
  }).observe($('facs'));
}

async function main() {
  readSettings();
  bindUi();
  applySettings();
  try {
    [index, toolkit] = await Promise.all([indexReady, loadVerovio()]);
    toolkit.setOptions(VEROVIO_OPTIONS);
    $('verovio-version').textContent = toolkit.getVersion();
    fillWorkSelect();
    await applyHash();
  } catch (error) {
    scoreMessage(error.message);
  }
}

main();
