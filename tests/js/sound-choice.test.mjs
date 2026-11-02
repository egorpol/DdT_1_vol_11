import test from 'node:test';
import assert from 'node:assert/strict';
import { SOUND_CHOICES, soundProgram, soundFile, needsConsent, restoredChoice, allSound } from '../../site/sound-choice.js';

const parts = [
  { role: 'violin', channel: 0, program: 40 },
  { role: 'viola_da_gamba', channel: 1, program: 42 },
  { role: 'figured_continuo_bass', channel: 2, program: 6 },
  { role: 'keyboard_realization', channel: 3, program: 6 },
];
const none = new Set();
test('encoded program and chosen sample are separate; files follow the sample', () => {
  const part = parts[0];
  assert.equal(soundProgram(part, 'encoded'), 40);
  assert.equal(soundFile(part, 'encoded'), 'violin-mp3.js');
  for (const [key, choice] of Object.entries(SOUND_CHOICES)) {
    assert.equal(soundProgram(part, key), choice.program);
    assert.equal(soundFile(part, key), choice.file);
  }
  assert.equal(part.program, 40);
  assert.equal(soundProgram(part, 'untrusted'), 40);
});
test('consent is per file; encoded set includes even muted parts, and harpsichord never asks here', () => {
  assert.equal(needsConsent(parts, parts[0], 'encoded', none), false);
  assert.equal(needsConsent(parts, parts[0], 'harpsichord', none), false);
  for (const key of ['piano', 'church_organ', 'string_ensemble']) {
    assert.equal(needsConsent(parts, parts[0], key, none), true);
    const agreed = new Set([SOUND_CHOICES[key].file]);
    for (const part of parts) assert.equal(needsConsent(parts, part, key, agreed), false);
  }
  // Generic rules still require consent when an edition has no encoded harpsichord.
  assert.equal(needsConsent([parts[0]], parts[0], 'harpsichord', none), true);
});
test('restored preference without consent remains visible but Play uses encoded', () => {
  assert.deepEqual(restoredChoice(parts, parts[0], { violin: 'piano' }, none), {
    key: 'piano', pending: true, playable: 'encoded',
  });
  assert.deepEqual(restoredChoice(parts, parts[0], { violin: 'piano' }, new Set(['acoustic_grand_piano-mp3.js'])), {
    key: 'piano', pending: false, playable: 'piano',
  });
  assert.equal(restoredChoice(parts, parts[0], { violin: 'harpsichord' }, none).playable, 'harpsichord');
  assert.equal(restoredChoice(parts, parts[0], { violin: 'constructor' }, none).playable, 'encoded');
});
test('All parts reports encoded, common actual sound, or Mixed', () => {
  assert.equal(allSound(), 'encoded');
  assert.equal(allSound(parts, {}), 'encoded');
  assert.equal(allSound(parts, { violin: 'piano' }), 'mixed');
  const choices = Object.fromEntries(parts.map((p) => [p.role, 'church_organ']));
  assert.equal(allSound(parts, choices), 'church_organ');
  assert.equal(allSound(parts, { violin: 'harpsichord', viola_da_gamba: 'harpsichord' }), 'harpsichord');
});
test('preferences follow roles across works, never reused channel numbers', () => {
  const other = [{ role: 'violin_1', channel: 0, program: 40 }, { role: 'violin', channel: 4, program: 40 }];
  const choices = { violin: 'piano' }, agreed = new Set(['acoustic_grand_piano-mp3.js']);
  assert.equal(restoredChoice(other, other[0], choices, agreed).playable, 'encoded');
  assert.equal(restoredChoice(other, other[1], choices, agreed).playable, 'piano');
});
