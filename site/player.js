/* Reusable, viewer-independent MIDI audio player (no edition or sample constants).
 * createPlayer({context, samples, onPosition(q), onEnd(), onSection(index),
 * onTempo({bpm, source, index})}) loads the pinned libraries; call it only after creating/resuming a native AudioContext in Play.
 * samples: object keyed by zero-based GM program, values {url, integrity}.
 * parseMidi(base64) returns a cacheable @tonejs/midi Midi. prepare(midi, parts)
 * loads instruments and returns an opaque score; parts are {channel, program}.
 * play(score, q, percent), pause() -> q, stop(q = 0), setTempo(percent),
 * setMuted(channels), setVolumes({channel: level}) (0–1, independent of mute),
 * setSections([{q, factor, index}]) (quarters, live replaceable), and position
 * (quarter notes) operate on one Transport. Sections are in performed-time order.
 * gains reports the last linear channel gains set (mute ? 0 : level); changes
 * ramp over 15 ms. tempo reports {bpm, source: guide/single/midi, index}.
 * Sections scale the first MIDI tempo; multiple MIDI tempo events override them.
 * tempoPlan(midi, sections, percent) is pure and returns {source, points} with
 * integer ticks, effective bpm and the host's section index (-1 without guide).
 * onSection/onTempo run at scheduling callbacks (up to lookAhead before audio).
 * onPosition runs on animation frames and reads Transport.ticks, never wall time.
 * Note releases are also scheduled in ticks, so held notes follow live tempo.
 * The host owns cancellation of async prepare results, state, persistence,
 * notation/time-map caching, highlighting, navigation and all user messages.
 */
const LIBRARIES = {
  tone: ['https://cdn.jsdelivr.net/npm/tone@15.1.22/build/Tone.js', 'sha384-NWoslxaf/3dYwQk+uGziDYJFdsjBpVlU1WpFRexuDFcIk/5PJpCbpVXia2Uikeix'],
  midi: ['https://cdn.jsdelivr.net/npm/@tonejs/midi@2.0.28/build/Midi.js', 'sha384-oayW9+sNK13nMFV3qwnFvUVk2XMCOleWoCgn4Ng3VLzGbgWNGDsc7RE4InhhvpQe'],
  smplr: ['https://cdn.jsdelivr.net/npm/smplr@1.1.0/dist/index.mjs', 'sha384-ERet/eSlh2t4/ufuKyI3+EZbTniGS3dWRRw4wHJZDSqOjrbaQ1Xwk+rB3gYt/+9W'],
};
let libraries;
const scripts = new Map();

function loadScript([url, integrity]) {
  if (!scripts.has(url)) {
    scripts.set(url, new Promise((resolve, reject) => {
      const script = document.createElement('script');
      Object.assign(script, { src: url, integrity, crossOrigin: 'anonymous' });
      script.onload = resolve;
      script.onerror = () => { script.remove(); reject(new Error(`Player library could not be loaded: ${url}`)); };
      document.head.append(script);
    }).catch((error) => { scripts.delete(url); throw error; }));
  }
  return scripts.get(url);
}

async function loadModule([url, integrity]) {
  const response = await fetch(url, { integrity, mode: 'cors' });
  if (!response.ok) throw new Error(`Player library: HTTP ${response.status}`);
  const objectUrl = URL.createObjectURL(new Blob([await response.blob()], { type: 'text/javascript' }));
  try { return await import(objectUrl); } finally { URL.revokeObjectURL(objectUrl); }
}

function loadLibraries() {
  if (!libraries) {
    libraries = Promise.all([loadScript(LIBRARIES.tone), loadScript(LIBRARIES.midi), loadModule(LIBRARIES.smplr)])
      .then(([, , smplr]) => ({ Tone: globalThis.Tone, Midi: globalThis.Midi, Soundfont: smplr.Soundfont }))
      .catch((error) => { libraries = null; throw error; });
  }
  return libraries;
}

export function tempoPlan(midi, sections = [], percent = 100) {
  const { ppq, tempos } = midi.header;
  const base = tempos[0]?.bpm || 120;
  const source = tempos.length > 1 ? 'midi' : sections.length ? 'guide' : 'single';
  const raw = source === 'midi' ? tempos.map((t) => ({ ticks: t.ticks, bpm: t.bpm, index: -1 }))
    : source === 'guide' ? sections.map((s, i) => ({ ticks: s.q * ppq, bpm: base * s.factor, index: s.index ?? i }))
      : [{ ticks: 0, bpm: base, index: -1 }];
  const points = [];
  for (const point of raw) {
    const next = { ...point, ticks: Math.round(point.ticks), bpm: point.bpm * percent / 100 };
    if (points.at(-1)?.ticks === next.ticks) points.pop();
    points.push(next);
  }
  if (points[0].ticks > 0) points.unshift({ ticks: 0, bpm: base * percent / 100, index: -1 });
  return { source, points };
}

export async function createPlayer({ context, samples, onPosition, onEnd, onSection = () => {}, onTempo = () => {} }) {
  const { Tone, Midi, Soundfont } = await loadLibraries();
  Tone.setContext(context);
  // Keep the scheduling horizon short; marks read the same Transport clock.
  Tone.getContext().lookAhead = 0.025;
  const transport = Tone.getTransport();
  const instruments = new Map();
  const voices = new Set();
  let score = null;
  let muted = new Set();
  let volumes = {};
  let gains = {};
  let sections = [];
  let percent = 100;
  let tempoEvents = [];
  let activeTick = 0;
  let planVersion = 0;
  let tempo = { bpm: 0, source: 'single', index: -1 };
  let frame = 0;
  let running = false;
  let voiceId = 0;

  function silence(channel) {
    for (const voice of voices) {
      if (channel === undefined || voice.channel === channel) { voice.stop(); voices.delete(voice); }
    }
  }

  function halt() {
    running = false;
    cancelAnimationFrame(frame);
    transport.stop();
    transport.cancel(0);
    tempoEvents = [];
    ++planVersion;
    silence();
  }

  async function instrument(channel, program) {
    const file = samples[program];
    if (!file?.url || !file.integrity) throw new Error(`No pinned sample file for GM program ${program}.`);
    const key = `${channel}:${program}`;
    if (!instruments.has(key)) {
      const gain = context.createGain();
      gain.connect(context.destination);
      const sound = new Soundfont(context, {
        instrumentUrl: file.url, destination: gain,
        storage: { fetch: (url) => fetch(url, { integrity: file.integrity, mode: 'cors' }) },
      });
      instruments.set(key, sound.ready.then(() => ({ sound, gain, channel })).catch((error) => {
        instruments.delete(key);
        sound.dispose();
        gain.disconnect();
        throw error;
      }));
    }
    return instruments.get(key);
  }

  function startNote(part, note, time) {
    if (muted.has(part.channel)) return null;
    const voice = { channel: part.channel, stop: null };
    // smplr otherwise uses the pitch as stopId: a release would also cut another
    // voice on the same pitch (including unisons on a shared MIDI channel).
    voice.stop = part.sound.start({ note: note.midi, velocity: note.velocity * 127, time,
      stopId: `midi-${++voiceId}`, ampRelease: 0.01,
      onEnded: () => voices.delete(voice) });
    voices.add(voice);
    return voice;
  }

  function applyGains() {
    if (!score) return;
    gains = {};
    for (const [channel, part] of score.channels) {
      const value = muted.has(channel) ? 0 : volumes[channel] ?? 1;
      gains[channel] = value;
      const param = part.gain.gain;
      const now = context.currentTime;
      param.cancelAndHoldAtTime(now);
      param.linearRampToValueAtTime(value, now + 0.015);
      if (muted.has(channel)) silence(channel);
    }
  }

  function report(point, source) {
    tempo = { bpm: point.bpm, source, index: point.index };
    // Update before calling the host: a synchronous live edit must see this point.
    activeTick = point.ticks;
    onTempo(tempo);
    onSection(point.index);
  }

  function updatePlan(from = activeTick) {
    if (!score) return;
    const version = ++planVersion;
    for (const id of tempoEvents) transport.clear(id);
    tempoEvents = [];
    const { source, points } = tempoPlan(score.midi, sections, percent);
    const point = points.findLast((p) => p.ticks <= from) || points[0];
    transport.bpm.value = point.bpm;
    report(point, source);
    if (!running || version !== planVersion) return;
    for (const next of points.filter((p) => p.ticks > from)) {
      tempoEvents.push(transport.schedule((time) => {
        if (version !== planVersion) return;
        transport.bpm.setValueAtTime(next.bpm, time);
        report(next, source);
      }, `${next.ticks}i`));
    }
  }

  const player = {
    parseMidi(base64) {
      return new Midi(Uint8Array.from(atob(base64), (c) => c.charCodeAt(0)));
    },
    async prepare(midi, parts) {
      const channels = new Map(await Promise.all(parts.map(async ({ channel, program }) =>
        [channel, await instrument(channel, program)])));
      for (const track of midi.tracks) {
        if (!track.notes.length) continue;
        if (!channels.has(track.channel)) throw new Error(`No part for MIDI channel ${track.channel}.`);
        const part = parts.find((p) => p.channel === track.channel);
        if (part.program !== track.instrument.number) throw new Error(`MIDI program differs on channel ${track.channel}.`);
      }
      return { midi, channels, end: midi.durationTicks / midi.header.ppq };
    },
    get position() { return score ? transport.ticks / score.midi.header.ppq : 0; },
    get gains() { return { ...gains }; },
    get tempo() { return { ...tempo }; },
    setTempo(value) { percent = value; updatePlan(); },
    setSections(value) { sections = value; updatePlan(Math.max(activeTick, transport.ticks)); },
    setVolumes(value) { volumes = { ...value }; applyGains(); },
    setMuted(channels) { muted = new Set(channels); applyGains(); },
    play(prepared, q, value) {
      halt();
      score = prepared;
      const ppq = score.midi.header.ppq;
      // Tone parses only whole ticks in '<n>i'; a fraction falls back to seconds.
      const from = Math.round(q * ppq);
      transport.PPQ = ppq;
      percent = value;
      player.setMuted(muted);
      transport.ticks = from;
      running = true;
      updatePlan(from);
      for (const track of score.midi.tracks) for (const note of track.notes) {
        const end = note.ticks + note.durationTicks;
        if (end <= from) continue;
        const part = score.channels.get(track.channel);
        let voice;
        transport.schedule((time) => { voice = startNote(part, note, time); }, `${Math.max(note.ticks, from)}i`);
        transport.schedule((time) => { voice?.stop(time); }, `${end}i`);
      }
      transport.start();
      const tick = () => {
        if (!running) return;
        const q = player.position;
        onPosition(q);
        if (q >= score.end) { player.stop(); onEnd(); return; }
        frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    },
    pause() {
      const q = player.position;
      halt();
      transport.ticks = q * score.midi.header.ppq;
      return q;
    },
    stop(q = 0) {
      halt();
      if (score) transport.ticks = q * score.midi.header.ppq;
    },
  };
  return player;
}
