import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { createChannelSounds, omitSilentSamples } from '../../site/player.js';

const SAMPLE_HEADER = `if (typeof(MIDI) === 'undefined') var MIDI = {};
if (typeof(MIDI.Soundfont) === 'undefined') MIDI.Soundfont = {};
MIDI.Soundfont.contrabass = {
`;
const SAMPLE_SOURCE = `${SAMPLE_HEADER}"A0": "data:audio/mp3;base64,QTA=",
"Bb2": "data:audio/mp3;base64,QmIy",
"B2": "data:audio/mp3;base64,QjI=",
"C3": "data:audio/mp3;base64,QzM=",
"Ab3": "data:audio/mp3;base64,QWIz",
"A3": "data:audio/mp3;base64,QTM=",
"Bb3": "data:audio/mp3;base64,QmIz",
"B3": "data:audio/mp3;base64,QjM=",
"C4": "data:audio/mp3;base64,QzQ=",
"Db4": "data:audio/mp3;base64,RGI0",
"E4": "data:audio/mp3;base64,RTQ=",
"Bb7": "data:audio/mp3;base64,QmI3",
"B7": "data:audio/mp3;base64,Qjc=",
"C8": "data:audio/mp3;base64,Qzg=",

}
`;
const HIGH_KEYS = ['Bb3', 'B3', 'C4', 'Db4', 'E4', 'Bb7', 'B7', 'C8'];

// Verbatim parser from the pinned smplr 1.1.0 dist/index.mjs.
function midiJsToJson(source) {
  const header = source.indexOf("MIDI.Soundfont.");
  if (header < 0) throw Error("Invalid MIDI.js Soundfont format");
  const start = source.indexOf("=", header) + 2;
  const end = source.lastIndexOf(",");
  return JSON.parse(source.slice(start, end) + "}");
}

function withoutKeys(keys) {
  const samples = midiJsToJson(SAMPLE_SOURCE);
  for (const key of keys) delete samples[key];
  return samples;
}

function fixture(fetchSample = () => Promise.resolve(new Response(new Uint8Array())), overrides = {}) {
  const instances = [], gains = [];
  const context = { destination: {}, createGain() {
    const gain = { connect() {}, disconnect() { this.disconnected = true; } };
    gains.push(gain); return gain;
  } };
  class Soundfont {
    constructor(context, options) {
      this.options = options;
      this.ready = new Promise((resolve, reject) => { this.resolve = resolve; this.reject = reject; });
      this.disposed = false;
      instances.push(this);
    }
    dispose() { assert.equal(this.disposed, false, 'dispose exactly once'); this.disposed = true; }
  }
  const samples = { ...Object.fromEntries([0, 6, 19, 40, 42, 48].map((p) => [p, { url: `sample-${p}`, integrity: 'pinned' }])), ...overrides };
  const scheduler = (ctx, options) => { assert.equal(options.lookaheadMs, 2000); return {}; };
  return { bank: createChannelSounds(context, samples, Soundfont, scheduler, fetchSample), instances, gains };
}
const turn = async () => { await new Promise((resolve) => setImmediate(resolve)); };
async function load(f, channel, program) {
  const pending = f.bank.select(channel, program);
  await turn(); f.instances.at(-1).resolve();
  assert.equal(await pending, true);
}
test('one shared gain, old tails retained until last voice ends, cycling frees every replaced sound', async () => {
  const f = fixture();
  await load(f, 0, 40);
  const old = f.bank.channels.get(0).record, voice = {};
  old.voices.add(voice);
  await load(f, 0, 0);
  assert.equal(f.gains.length, 1);
  assert.equal(f.instances[0].options.destination, f.instances[1].options.destination);
  assert.equal(f.instances[0].disposed, false, 'tail must finish');
  f.bank.ended(old, voice);
  assert.equal(f.instances[0].disposed, true);
  assert.equal(old.sound, null, 'drop AudioBuffer owner');
  for (const p of [6, 19, 48, 40]) await load(f, 0, p);
  assert.equal(f.instances.filter((s) => !s.disposed).length, 1);
  f.bank.release();
  assert.equal(f.instances.filter((s) => !s.disposed).length, 0);
  assert.equal(f.gains[0].disconnected, true);
});
test('Piano then organ: obsolete load finishes, is disposed, and never replaces the old sound', async () => {
  const f = fixture(); await load(f, 0, 40);
  const piano = f.bank.select(0, 0); await turn();
  const organ = f.bank.select(0, 19); await turn();
  assert.equal(f.instances.length, 2, 'one candidate decode per channel');
  f.instances[1].resolve();
  assert.equal(await piano, false);
  assert.deepEqual(f.bank.sounds, { 0: 40 });
  await turn();
  assert.equal(f.instances[1].disposed, true);
  f.instances[2].resolve(); assert.equal(await organ, true);
  assert.deepEqual(f.bank.sounds, { 0: 19 });
});
test('Stop cancellation, fresh Play and a work switch cannot apply an old load', async () => {
  const f = fixture(); await load(f, 0, 40);
  const stopped = f.bank.select(0, 0); await turn(); f.bank.cancel();
  f.instances[1].resolve(); assert.equal(await stopped, false);
  assert.deepEqual(f.bank.sounds, { 0: 40 });
  const switching = f.bank.select(0, 19); await turn();
  f.bank.release();
  await load(f, 0, 42);
  f.instances[2].resolve(); assert.equal(await switching, false);
  assert.deepEqual(f.bank.sounds, { 0: 42 });
  assert.equal(f.instances.filter((s) => !s.disposed).length, 1);
});
test('failed candidate keeps the old instance and gain; latest selection can retry', async () => {
  const f = fixture(); await load(f, 0, 40);
  const failed = f.bank.select(0, 48);
  const rejection = assert.rejects(failed, /network blocked/);
  await turn(); f.instances[1].reject(new Error('network blocked')); await rejection;
  assert.deepEqual(f.bank.sounds, { 0: 40 });
  assert.equal(f.instances[1].disposed, true);
  await load(f, 0, 19);
  assert.deepEqual(f.bank.sounds, { 0: 19 });
});

test('a newer download can finish and apply before an older response arrives', async () => {
  let finishPiano;
  const requested = [];
  const f = fixture((url) => {
    requested.push(url);
    return url === 'sample-0' ? new Promise((resolve) => { finishPiano = resolve; }) : Promise.resolve(new Response());
  });
  await load(f, 0, 40);
  const piano = f.bank.select(0, 0); await turn();
  assert.equal(f.instances.length, 1, 'no obsolete Soundfont allocated for a pending response');
  await load(f, 0, 19);
  assert.deepEqual(f.bank.sounds, { 0: 19 });
  finishPiano(new Response());
  assert.equal(await piano, false);
  assert.deepEqual(f.bank.sounds, { 0: 19 });
  assert.deepEqual(requested, ['sample-40', 'sample-0', 'sample-19']);
});

test('All parts shares one pinned file request across channels, and retries after HTTP failure', async () => {
  let finish;
  const requests = [];
  const f = fixture((url, options) => {
    requests.push({ url, options });
    return new Promise((resolve) => { finish = resolve; });
  });
  const first = f.bank.select(0, 19), second = f.bank.select(1, 19);
  assert.equal(requests.length, 1);
  assert.deepEqual(requests[0].options, { integrity: 'pinned', mode: 'cors' });
  finish(new Response('bytes'));
  await turn();
  assert.equal(f.instances.length, 2);
  for (const instance of f.instances) instance.resolve();
  assert.deepEqual(await Promise.all([first, second]), [true, true]);
  assert.deepEqual(f.bank.sounds, { 0: 19, 1: 19 });
  const failed = f.bank.select(0, 48);
  const rejected = assert.rejects(failed, /Sample HTTP 503/);
  finish(new Response('', { status: 503 })); await rejected;
  assert.equal(f.bank.sounds[0], 19);
  const retry = f.bank.select(0, 48);
  assert.equal(requests.length, 3, 'a failed file must not poison retries');
  finish(new Response('bytes')); await turn(); f.instances.at(-1).resolve();
  assert.equal(await retry, true);
});

test('omitSilentSamples removes only whole listed keys and preserves smplr-parsed sample data', () => {
  const bytes = new TextEncoder().encode(SAMPLE_SOURCE).buffer;
  for (const keys of [['B3'], ['C4'], ['B3', 'C4', 'missing'], ['missing']]) {
    const source = new TextDecoder().decode(omitSilentSamples(bytes, keys));
    assert.deepEqual(midiJsToJson(source), withoutKeys(keys));
    assert.ok(source.startsWith(SAMPLE_HEADER), 'keep the MIDI.js header');
    assert.ok(source.endsWith('\n\n}\n'), 'keep the closing brace');
  }
});

test('omitSilentSamples keeps A3\'s trailing comma when all higher entries including C8 are removed', () => {
  const bytes = new TextEncoder().encode(SAMPLE_SOURCE).buffer;
  const source = new TextDecoder().decode(omitSilentSamples(bytes, HIGH_KEYS));
  assert.match(source, /"A3": "data:audio\/mp3;base64,QTM=",\n\n}\n$/);
  assert.deepEqual(midiJsToJson(source), withoutKeys(HIGH_KEYS));
});

test('omitSilentSamples returns unlisted bytes by identity and never mutates shared input', () => {
  const bytes = new TextEncoder().encode(SAMPLE_SOURCE).buffer;
  const original = new Uint8Array(bytes).slice();
  assert.equal(omitSilentSamples(bytes), bytes);
  assert.equal(omitSilentSamples(bytes, []), bytes);
  assert.notEqual(omitSilentSamples(bytes, HIGH_KEYS), bytes);
  assert.deepEqual(new Uint8Array(bytes), original);
});

test('select filters listed samples for both channels sharing a pinned file request', async () => {
  let finish;
  const requests = [];
  const bytes = new TextEncoder().encode(SAMPLE_SOURCE).buffer;
  const original = new Uint8Array(bytes).slice();
  const f = fixture((url, options) => {
    requests.push({ url, options });
    return new Promise((resolve) => { finish = resolve; });
  }, { 43: { url: 'sample-43', integrity: 'pinned', silent: HIGH_KEYS } });
  const first = f.bank.select(0, 43), second = f.bank.select(1, 43);
  assert.deepEqual(requests, [{ url: 'sample-43', options: { integrity: 'pinned', mode: 'cors' } }]);
  finish({ ok: true, arrayBuffer: async () => bytes });
  await turn();
  assert.equal(f.instances.length, 2);
  const sources = [];
  for (const instance of f.instances) {
    const response = await instance.options.storage.fetch();
    sources.push(await response.text());
    assert.deepEqual(midiJsToJson(sources.at(-1)), withoutKeys(HIGH_KEYS));
    instance.resolve();
  }
  assert.equal(sources[0], sources[1]);
  assert.deepEqual(new Uint8Array(bytes), original);
  assert.deepEqual(await Promise.all([first, second]), [true, true]);
});

test('select passes unlisted sample bytes unchanged to Soundfont storage', async () => {
  const bytes = new TextEncoder().encode(SAMPLE_SOURCE).buffer;
  const f = fixture(async () => ({ ok: true, arrayBuffer: async () => bytes }));
  await load(f, 0, 19);
  const response = await f.instances[0].options.storage.fetch();
  assert.deepEqual(new Uint8Array(await response.arrayBuffer()), new Uint8Array(bytes));
});

test('viewer contrabass silent list is exactly the 51 flat-spelled keys from MIDI 58 to 108', (t) => {
  const viewer = readFileSync(new URL('../../site/viewer.js', import.meta.url), 'utf8');
  const block = viewer.match(/const SAMPLE_FILES = \{[\s\S]*?\n\};/);
  assert.ok(block, 'SAMPLE_FILES is defined inline');
  const samples = runInNewContext(`${block[0]}\nSAMPLE_FILES;`, { SOUNDFONT_ROOT: 'pinned/' });
  const names = Array.from(samples[43].silent);
  const pitches = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];
  const expected = Array.from({ length: 51 }, (_, i) => {
    const midi = i + 58;
    return pitches[midi % 12] + (Math.floor(midi / 12) - 1);
  });
  assert.deepEqual(names, expected);
  assert.equal(names.length, 51);
  assert.equal(names[0], 'Bb3');
  assert.equal(names.at(-1), 'C8');
  assert.deepEqual(Object.keys(samples).filter((program) => 'silent' in samples[program]), ['43']);
  t.diagnostic(`Read ${names.length} names from viewer.js: first ${names[0]}, last ${names.at(-1)}`);
});
