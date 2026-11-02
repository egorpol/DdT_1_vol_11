import test from 'node:test';
import assert from 'node:assert/strict';
import { audibleTick, dueNotifications } from '../../site/player.js';

test('new Play clamps the previous run until its audio start, including an old end', () => {
  assert.equal(audibleTick(true, 0, 10.3, 10, 50000), 0);
  assert.equal(audibleTick(true, 9600, 10.3, 10.299, 224), 9600);
  assert.equal(audibleTick(true, 9600, 10.3, 10.3, 9600), 9600);
  assert.equal(audibleTick(true, 9600, 10.3, 10.4, 9620), 9620);
});

test('pause/stop expose the stored audible tick, regardless of Transport history', () => {
  assert.equal(audibleTick(false, 123, 10.3, 100, 99999), 123);
  assert.equal(audibleTick(false, 0, 10.3, 100, 99999), 0);
});

const event = (time, version, bpm = 48) => ({ time, version, tempo: { bpm, index: 1, source: 'guide' } });
test('notifications wait for audio time, in order, without expiration on late frames', () => {
  const queue = [event(3, 1), event(1, 1, 102), event(2, 1)];
  assert.deepEqual(dueNotifications(queue, .9, 1), { due: [], pending: [queue[1], queue[2], queue[0]] });
  assert.deepEqual(dueNotifications(queue, 2, 1), { due: [queue[1], queue[2]], pending: [queue[0]] });
  assert.deepEqual(dueNotifications(queue, 100, 1), { due: [queue[1], queue[2], queue[0]], pending: [] });
  assert.deepEqual(queue.map(e => e.time), [3, 1, 2], 'pure helper must not mutate its input');
});

test('halt and every plan edit discard stale notifications, even before they are due', () => {
  const oldBoundary = event(10.3, 1, 48);
  assert.deepEqual(dueNotifications([oldBoundary], 10.2, 2), { due: [], pending: [] });
  // A live slider/guide edit between scheduling and audio must stay at its new
  // value: the boundary's old 48 bpm can never overwrite the immediate 24 bpm.
  assert.deepEqual(dueNotifications([oldBoundary, event(11, 2, 24)], 10.4, 2), {
    due: [], pending: [event(11, 2, 24)],
  });
  assert.deepEqual(dueNotifications([oldBoundary], 100, 3), { due: [], pending: [] });
});

test('equal-time notifications retain scheduling order', () => {
  const queue = [event(1, 1, 48), event(1, 1, 24)];
  assert.deepEqual(dueNotifications(queue, 1, 1).due, queue);
});
