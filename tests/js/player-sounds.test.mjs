import test from 'node:test';
import assert from 'node:assert/strict';
import { createChannelSounds } from '../../site/player.js';

function fixture(fetchSample = () => Promise.resolve(new Response(new Uint8Array()))) {
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
  const samples = Object.fromEntries([0, 6, 19, 40, 42, 48].map((p) => [p, { url: `sample-${p}`, integrity: 'pinned' }]));
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
