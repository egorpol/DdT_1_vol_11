import test from 'node:test';
import assert from 'node:assert/strict';
import { fillListenerParams, holdAt } from '../../site/player.js';

const LISTENER = { positionX: 0, positionY: 0, positionZ: 0, forwardX: 0, forwardY: 0, forwardZ: -1, upX: 0, upY: 1, upZ: 0 };

function sourceContext(listener) {
  const offsets = [];
  return { listener, offsets, createConstantSource() { const offset = { value: 1 }; offsets.push(offset); return { offset }; } };
}

test('Firefox listener without params gets stand-ins with Tone defaults, once', () => {
  const context = sourceContext({});
  fillListenerParams(context);
  assert.equal(context.offsets.length, 9);
  assert.deepEqual(Object.fromEntries(Object.keys(LISTENER).map((name) => [name, context.listener[name].value])), LISTENER);
  assert.deepEqual(new Set(Object.keys(LISTENER).map((name) => context.listener[name])), new Set(context.offsets));
  fillListenerParams(context); // Play retried on the same context
  assert.equal(context.offsets.length, 9);
});

test('native listener params are kept', () => {
  const native = Object.fromEntries(Object.keys(LISTENER).map((name) => [name, { value: 5 }]));
  const context = sourceContext({ ...native });
  fillListenerParams(context);
  assert.equal(context.offsets.length, 0);
  for (const name of Object.keys(LISTENER)) assert.equal(context.listener[name], native[name]);
});

function automation(withHold) {
  const calls = [];
  const param = {
    value: 0.4,
    cancelScheduledValues: (time) => calls.push(['cancel', time]),
    setValueAtTime: (value, time) => calls.push(['set', value, time]),
  };
  if (withHold) param.cancelAndHoldAtTime = (time) => calls.push(['hold', time]);
  return { param, calls };
}

test('holdAt uses cancelAndHoldAtTime where the browser has it', () => {
  const { param, calls } = automation(true);
  holdAt(param, 2.5);
  assert.deepEqual(calls, [['hold', 2.5]]);
});

test('holdAt anchors the current value where cancelAndHoldAtTime is missing (Firefox)', () => {
  const { param, calls } = automation(false);
  holdAt(param, 2.5);
  assert.deepEqual(calls, [['cancel', 2.5], ['set', 0.4, 2.5]]);
});
