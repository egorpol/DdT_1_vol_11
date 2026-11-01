import test from 'node:test';
import assert from 'node:assert/strict';
import { tempoPlan } from '../../site/player.js';
import { mapTempoSections } from '../../site/tempo-map.js';

const midi = { header: { ppq: 120, tempos: [{ bpm: 120, ticks: 0 }] } };
const sections = [{ q: 0, factor: .85 }, { q: 108, factor: .4 }];
test('one MIDI tempo: guide factors at 100% and 50%', () => {
  assert.deepEqual(tempoPlan(midi, sections, 100), { source: 'guide', points: [
    { ticks: 0, bpm: 102, index: 0 }, { ticks: 12960, bpm: 48, index: 1 },
  ] });
  assert.deepEqual(tempoPlan(midi, sections, 50).points.map(p => p.bpm), [51, 24]);
  assert.deepEqual(tempoPlan(midi, [], 100), { source: 'single', points: [{ ticks: 0, bpm: 120, index: -1 }] });
});
test('encoded MIDI tempo changes override guide, with global scaling', () => {
  const encoded = { header: { ppq: 120, tempos: [{ bpm: 120, ticks: 0 }, { bpm: 60, ticks: 480 }] } };
  assert.deepEqual(tempoPlan(encoded, sections, 50), { source: 'midi', points: [
    { ticks: 0, bpm: 60, index: -1 }, { ticks: 480, bpm: 30, index: -1 },
  ] });
});
test('tempo boundaries use whole ticks, including fractional quarters', () => {
  assert.equal(tempoPlan(midi, [{ q: 0, factor: 1 }, { q: 4 / 3, factor: .5 }]).points[1].ticks, 160);
  assert.equal(tempoPlan(midi, [{ q: 0, factor: 1 }, { q: 2.001, factor: .5 }]).points[1].ticks, 240);
});
const measures = ['a', 'b', 'c', 'd', 'e'];
const starts = new Map(measures.map((m, i) => [m, i * 4]));
const row = (measure, offset = 0) => ({ measure, offset });
const events = entries => entries.map(([measure, qstamp]) => ({ measure, qstamp }));
const map = (rows, entries) => mapTempoSections(rows, measures, events(entries), starts);
test('notated order, exact first-pass starts and no duplicate consecutive changes', () => {
  assert.deepEqual(map([row('a'), row('c')], [['a', .5], ['a', 1], ['b', 4], ['c', 8], ['d', 12]]), [
    { q: 0, index: 0 }, { q: 8, index: 1 },
  ]);
});
test('mid-measure row keeps preceding section until its offset', () => {
  assert.deepEqual(map([row('a'), row('c', 3)], [['a', 0], ['b', 4], ['c', 8], ['d', 12]]), [
    { q: 0, index: 0 }, { q: 11, index: 1 },
  ]);
});
test('repeat re-enters a row measure, including its mid-bar boundary', () => {
  assert.deepEqual(map([row('a'), row('b', 2)], [['a', 0], ['b', 4], ['c', 8], ['b', 12], ['c', 16]]), [
    { q: 0, index: 0 }, { q: 6, index: 1 }, { q: 12, index: 0 }, { q: 14, index: 1 },
  ]);
});
test('repeat jumps into middle of an earlier section, not its opening row', () => {
  assert.deepEqual(map([row('a'), row('d')], [['a', 0], ['b', 4], ['c', 8], ['d', 12], ['e', 16], ['b', 20], ['c', 24], ['d', 28]]), [
    { q: 0, index: 0 }, { q: 12, index: 1 }, { q: 20, index: 0 }, { q: 28, index: 1 },
  ]);
});
