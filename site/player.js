/* Reusable, viewer-independent MIDI audio player (no edition or sample constants).
 * createPlayer({context, samples, onPosition(q), onEnd(), onSection(index),
 * onTempo({bpm, source, index})}) loads the pinned libraries; call it only after creating/resuming a native AudioContext in Play.
 * samples: object keyed by zero-based GM program, values {url, integrity, silent?}.
 * Optional silent is an array of key names whose samples are left out, so smplr's
 * nearest-key spread covers their range.
 * parseMidi(base64) returns a cacheable @tonejs/midi Midi. prepare(midi, parts)
 * loads instruments and returns an opaque score; parts are {channel, program, sound},
 * where program must match the MIDI and sound is the sample GM program (default program).
 * play(score, q, percent), pause() -> q, stop(q = 0), setTempo(percent),
 * setMuted(channels), setVolumes({channel: level}) (0–1, independent of mute),
 * setSections([{q, factor, index}]) (quarters, live replaceable), and position
 * (quarter notes) operate on one Transport. Sections are in performed-time order.
 * setSound(channel, program) -> Promise<boolean> hot swaps a prepared channel;
 * true means applied, false means superseded/cancelled. sounds reports channel ->
 * sample GM program in use on the playing score's channels ({} before the first play).
 * Stop/pause/play/prepare invalidate pending swaps. prepare keeps a channel's decoded
 * sound when the next score uses the same one; release() stops and frees every channel.
 * Swaps leave Transport running; attacks already handed off in the 0.3 s horizon
 * keep their old sound. Old voices finish through the same channel gain; their
 * Soundfont is disposed on the last voice end. Loads serialize per channel, so
 * obsolete candidates are disposed before another starts. Failed swaps keep the old
 * sound and reject. The host must authorize every sample before prepare/setSound.
 * gains reports the last linear channel gains set (mute ? 0 : level); changes
 * ramp over 15 ms. tempo reports {bpm, source: guide/single/midi, index}.
 * Sections scale the first MIDI tempo; multiple MIDI tempo events override them.
 * tempoPlan(midi, sections, percent) is pure and returns {source, points} with
 * integer ticks, effective bpm and the host's section index (-1 without guide).
 * onSection/onTempo run at audio time on frames (late frames never expire them);
 * live edits report immediately. Halt/plan edits discard pending notifications.
 * onPosition reads ticks at AudioContext.currentTime on animation frames, held
 * at the requested start until audio starts; stopped/paused position is stored.
 * Play/tempo/guide edits sound about 0.3 s later; pause/stop/mute/gain are immediate.
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
// Tone must hand notes to Web Audio ~0.275–0.3 s ahead, protecting page turns.
// Set updateInterval AFTER lookAhead: Tone's setter sets it to half the horizon.
const LOOK_AHEAD = 0.3;
const UPDATE_INTERVAL = 0.025;
// Wider than Tone's horizon: smplr dispatches immediately instead of queuing on
// its main-thread 50 ms timer (whose default horizon would cap ours at 0.2 s).
const SAMPLE_LOOK_AHEAD_MS = 2000;

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
      .then(([, , smplr]) => ({ Tone: globalThis.Tone, Midi: globalThis.Midi, Soundfont: smplr.Soundfont, Scheduler: smplr.Scheduler }))
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

// Tone extrapolates the previous run before a newly scheduled start, even after
// ticks is assigned. Never expose those ticks or use them for end detection.
export function audibleTick(running, storedTick, startTime, now, ticks) {
  return !running || now < startTime ? storedTick : ticks;
}

// No expiry: even a background tab must deliver every current-plan boundary in
// audio-time order when frames resume. Versions also invalidate live-edit races.
export function dueNotifications(queue, now, version) {
  const current = queue.filter((item) => item.version === version).sort((a, b) => a.time - b.time);
  return { due: current.filter((item) => item.time <= now), pending: current.filter((item) => item.time > now) };
}

// Tone 15.1.22's Clock can run one tick twice: forEachTickBetween adds tick durations
// up to the end of one update and recomputes the next update's first tick with
// ceil(), so floating-point drift can put the same tick in both (4 of 14,168 ticks
// in 100 s of Op. II/2). Every Transport callback with an effect must run once.
export function once(callback) {
  let done = false;
  return (...args) => {
    if (done) return;
    done = true;
    callback(...args);
  };
}

// A second start would replace the voice the release refers to, so the first voice
// rang for its whole sample. Returns false for a note that ends before `from`.
export function scheduleNote(transport, note, from, start) {
  const end = note.ticks + note.durationTicks;
  if (end <= from) return false;
  let voice = null;
  transport.schedule(once((time) => { voice = start(time); }), `${Math.max(note.ticks, from)}i`);
  transport.schedule((time) => { voice?.stop(time); }, `${end}i`);
  return true;
}

// MIDI.js files have one quoted sample per line. Remove whole entries so the
// last kept sample retains the trailing comma required by smplr 1.1.0's parser.
export function omitSilentSamples(bytes, silent) {
  if (!silent?.length) return bytes;
  const keys = new Set(silent);
  const source = new TextDecoder().decode(bytes).replace(
    /^"([^"]+)": "[^"\r\n]*",\r?\n/gm,
    (entry, key) => keys.has(key) ? '' : entry,
  );
  return new TextEncoder().encode(source).buffer;
}

// Separate from Transport so lifecycle/race contracts can be tested with small audio doubles.
export function createChannelSounds(context, samples, Soundfont, Scheduler, fetchSample = fetch) {
  const channels = new Map();
  const requests = new Map();
  function dispose(record) {
    if (record.retired && !record.voices.size && record.sound) {
      record.sound.dispose();
      record.sound = null;
    }
  }
  function retire(record) { if (record) { record.retired = true; dispose(record); } }
  function cancel(part) {
    ++part.version;
    // Stop an obsolete candidate's own scheduler immediately, even if its
    // decode has not settled. smplr may then reject ready; the task handles it.
    if (part.candidate && !part.candidate.disposed) {
      part.candidate.sound.dispose();
      part.candidate.disposed = true;
    }
  }
  function slot(channel) {
    if (!channels.has(channel)) {
      const gain = context.createGain();
      gain.connect(context.destination);
      channels.set(channel, { channel, gain, record: null, candidate: null, version: 0, task: Promise.resolve() });
    }
    return channels.get(channel);
  }
  function fetchFile(file) {
    // Share only an in-flight file, never decoded AudioBuffers. Buffer its bytes
    // before creating a Soundfont: a slow obsolete download must not hold up the
    // latest choice or allocate an instrument. Browser caching handles later loads.
    if (!requests.has(file.url)) {
      const request = fetchSample(file.url, { integrity: file.integrity, mode: 'cors' }).then((response) => {
        if (!response.ok) throw new Error(`Sample HTTP ${response.status}: ${file.url}`);
        return response.arrayBuffer();
      });
      requests.set(file.url, request);
      const clear = () => { if (requests.get(file.url) === request) requests.delete(file.url); };
      request.then(clear, clear);
    }
    return requests.get(file.url);
  }
  function select(channel, program) {
    const part = slot(channel);
    cancel(part);
    const version = part.version;
    const valid = () => channels.get(channel) === part && version === part.version;
    if (part.record?.program === program) return Promise.resolve(true);
    const file = samples[program];
    if (!file?.url || !file.integrity) return Promise.reject(new Error(`No pinned sample file for GM program ${program}.`));
    const task = fetchFile(file).then((bytes) => {
      if (!valid()) return false;
      // Serialize only decoding, not downloads. Thus organ can take effect
      // while an older file response is still arriving.
      const decode = part.task.catch(() => {}).then(async () => {
        if (!valid()) return false;
        const sampleBytes = omitSilentSamples(bytes, file.silent);
        const sound = new Soundfont(context, {
          instrumentUrl: file.url, destination: part.gain,
          scheduler: Scheduler(context, { lookaheadMs: SAMPLE_LOOK_AHEAD_MS }),
          storage: { fetch: () => Promise.resolve(new Response(sampleBytes)) },
        });
        const candidate = { sound, disposed: false };
        part.candidate = candidate;
        try { await sound.ready; }
        catch (error) {
          if (!candidate.disposed) sound.dispose();
          if (valid()) throw error;
          return false;
        } finally { if (part.candidate === candidate) part.candidate = null; }
        if (!valid()) { if (!candidate.disposed) sound.dispose(); return false; }
        const previous = part.record;
        part.record = { sound, program, voices: new Set(), retired: false };
        retire(previous);
        return true;
      });
      part.task = decode;
      return decode;
    }).catch((error) => { if (valid()) throw error; return false; });
    return task;
  }
  return {
    channels, select,
    cancel() { for (const part of channels.values()) cancel(part); },
    release() {
      for (const part of channels.values()) {
        cancel(part);
        retire(part.record);
        part.record = null;
        part.gain.disconnect();
      }
      channels.clear();
    },
    ended(record, voice) { record.voices.delete(voice); dispose(record); },
    get sounds() { return Object.fromEntries([...channels].filter(([, p]) => p.record).map(([c, p]) => [c, p.record.program])); },
  };
}

// Tone's Listener wraps these AudioListener params on every context. Firefox has
// none; standardized-audio-context fills them in only for contexts it creates, so
// a native context fails "param must be an AudioParam". The player never pans in
// 3D: unstarted ConstantSourceNode offsets stand in and are never heard.
const LISTENER_PARAMS = { positionX: 0, positionY: 0, positionZ: 0, forwardX: 0, forwardY: 0, forwardZ: -1, upX: 0, upY: 1, upZ: 0 };

export function fillListenerParams(context) {
  const { listener } = context;
  for (const [name, value] of Object.entries(LISTENER_PARAMS)) {
    if (listener[name]) continue;
    const { offset } = context.createConstantSource();
    offset.value = value;
    Object.defineProperty(listener, name, { value: offset, configurable: true });
  }
}

// Firefox lacks cancelAndHoldAtTime; anchoring the current value is enough for 15 ms ramps.
export function holdAt(param, time) {
  if (typeof param.cancelAndHoldAtTime === 'function') param.cancelAndHoldAtTime(time);
  else { param.cancelScheduledValues(time); param.setValueAtTime(param.value, time); }
}

export async function createPlayer({ context, samples, onPosition, onEnd, onSection = () => {}, onTempo = () => {} }) {
  const { Tone, Midi, Soundfont, Scheduler } = await loadLibraries();
  fillListenerParams(context);
  Tone.setContext(context);
  Tone.getContext().lookAhead = LOOK_AHEAD;
  Tone.getContext().updateInterval = UPDATE_INTERVAL;
  const transport = Tone.getTransport();
  const instruments = createChannelSounds(context, samples, Soundfont, Scheduler);
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
  let notifications = [];
  let tempo = { bpm: 0, source: 'single', index: -1 };
  let frame = 0;
  let running = false;
  let storedTick = 0;
  let startTime = Infinity;
  let voiceId = 0;

  function silence(channel) {
    for (const voice of voices) {
      if (channel === undefined || voice.channel === channel) { voice.stop(); voices.delete(voice); }
    }
  }

  function halt() {
    instruments.cancel();
    running = false;
    startTime = Infinity;
    cancelAnimationFrame(frame);
    transport.stop();
    transport.cancel(0);
    tempoEvents = [];
    ++planVersion;
    notifications = [];
    silence();
  }

  function startNote(part, note, time) {
    if (muted.has(part.channel)) return null;
    const record = part.record;
    let stop;
    const voice = { channel: part.channel, stop: (time) => stop?.(time) };
    // Unique stopIds protect unisons. Clear the stop closure on natural sample
    // end too: a later tick release must never call a disposed old Soundfont.
    stop = record.sound.start({ note: note.midi, velocity: note.velocity * 127, time,
      stopId: `midi-${++voiceId}`, ampRelease: 0.01,
      onEnded: () => { stop = null; voices.delete(voice); instruments.ended(record, voice); } });
    record.voices.add(voice);
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
      holdAt(param, now);
      param.linearRampToValueAtTime(value, now + 0.015);
      if (muted.has(channel)) silence(channel);
    }
  }

  function notify(value, version = planVersion) {
    onTempo(value);
    if (version === planVersion) onSection(value.index);
  }

  function report(point, source, time) {
    tempo = { bpm: point.bpm, source, index: point.index };
    // Update scheduler state immediately: a live edit inside the lookahead window
    // must see this boundary, even though the host has not heard about it yet.
    activeTick = point.ticks;
    if (time === undefined) notify(tempo);
    else notifications.push({ time, version: planVersion, tempo });
  }

  function updatePlan(from = activeTick) {
    if (!score) return;
    const version = ++planVersion;
    notifications = [];
    for (const id of tempoEvents) transport.clear(id);
    tempoEvents = [];
    const { source, points } = tempoPlan(score.midi, sections, percent);
    const point = points.findLast((p) => p.ticks <= from) || points[0];
    transport.bpm.value = point.bpm;
    report(point, source);
    if (!running || version !== planVersion) return;
    for (const next of points.filter((p) => p.ticks > from)) {
      tempoEvents.push(transport.schedule(once((time) => {
        if (version !== planVersion) return;
        transport.bpm.setValueAtTime(next.bpm, time);
        report(next, source, time);
      }), `${next.ticks}i`));
    }
  }

  const player = {
    parseMidi(base64) {
      return new Midi(Uint8Array.from(atob(base64), (c) => c.charCodeAt(0)));
    },
    async prepare(midi, parts) {
      instruments.cancel();
      for (const track of midi.tracks) {
        if (!track.notes.length) continue;
        const part = parts.find((p) => p.channel === track.channel);
        if (!part) throw new Error(`No part for MIDI channel ${track.channel}.`);
        if (part.program !== track.instrument.number) throw new Error(`MIDI program differs on channel ${track.channel}.`);
      }
      await Promise.all(parts.map(({ channel, program, sound = program }) => instruments.select(channel, sound)));
      const channels = new Map(parts.map(({ channel }) => [channel, instruments.channels.get(channel)]));
      return { midi, channels, end: midi.durationTicks / midi.header.ppq };
    },
    get position() {
      if (!score) return 0;
      const now = context.currentTime;
      return audibleTick(running, storedTick, startTime, now, transport.getTicksAtTime(now)) / score.midi.header.ppq;
    },
    setSound(channel, program) {
      if (!score?.channels.has(channel)) return Promise.reject(new Error(`No prepared channel ${channel}.`));
      return instruments.select(channel, program);
    },
    get sounds() {
      if (!score) return {};
      return Object.fromEntries(Object.entries(instruments.sounds).filter(([channel]) => score.channels.has(+channel)));
    },
    release() { halt(); instruments.release(); score = null; },
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
      storedTick = from;
      running = true;
      updatePlan(from);
      for (const track of score.midi.tracks) {
        const part = score.channels.get(track.channel);
        for (const note of track.notes) scheduleNote(transport, note, from, (time) => startNote(part, note, time));
      }
      startTime = context.currentTime + LOOK_AHEAD;
      transport.start(startTime);
      const tick = () => {
        if (!running) return;
        const now = context.currentTime;
        const q = player.position;
        onPosition(q);
        // Use our frame loop instead of Tone Draw: no expiry can lose a boundary.
        // Use the frame's audio time: a blocking host page turn must not deliver
        // a boundary beyond the position just reported to that host.
        const { due, pending } = dueNotifications(notifications, now, planVersion);
        notifications = pending;
        for (const item of due) {
          if (running && item.version === planVersion) notify(item.tempo);
        }
        if (!running) return;
        if (now >= startTime && q >= score.end) { player.stop(); onEnd(); return; }
        frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    },
    pause() {
      const q = player.position;
      halt();
      storedTick = q * score.midi.header.ppq;
      transport.ticks = storedTick;
      return q;
    },
    stop(q = 0) {
      halt();
      storedTick = score ? q * score.midi.header.ppq : 0;
      if (score) transport.ticks = storedTick;
    },
  };
  return player;
}
