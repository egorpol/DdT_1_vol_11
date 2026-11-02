// Viewer sound choices and consent rules. No I/O: safe to import in node tests.
export const SOUND_CHOICES = {
  piano: { program: 0, label: 'Piano', file: 'acoustic_grand_piano-mp3.js', mb: '1.7' },
  harpsichord: { program: 6, label: 'Harpsichord', file: 'harpsichord-mp3.js', mb: '1.4' },
  church_organ: { program: 19, label: 'Church organ', file: 'church_organ-mp3.js', mb: '1.7' },
  string_ensemble: { program: 48, label: 'String ensemble', file: 'string_ensemble_1-mp3.js', mb: '1.8' },
};
export const ENCODED_SOUNDS = {
  40: { label: 'violin', file: 'violin-mp3.js' },
  42: { label: 'cello', file: 'cello-mp3.js' },
  43: { label: 'contrabass', file: 'contrabass-mp3.js' },
  6: { label: 'harpsichord', file: 'harpsichord-mp3.js' },
};
export function soundKey(value) {
  return Object.hasOwn(SOUND_CHOICES, value) ? value : 'encoded';
}
export function soundProgram(part, key) {
  return SOUND_CHOICES[soundKey(key)]?.program ?? part.program;
}
export function soundFile(part, key) {
  return SOUND_CHOICES[soundKey(key)]?.file ?? ENCODED_SOUNDS[part.program]?.file;
}
export function needsConsent(parts, part, key, agreed) {
  const file = soundFile(part, key);
  return !!file && !parts.some((p) => soundFile(p, 'encoded') === file) && !agreed.has(file);
}
// Restoring a preference cannot authorize a request. Play keeps the encoded sound.
export function restoredChoice(parts, part, choices, agreed) {
  const key = soundKey(choices[part.role]);
  const pending = needsConsent(parts, part, key, agreed);
  return { key, pending, playable: pending ? 'encoded' : key };
}
export function allSound(parts = [], choices = {}) {
  if (!parts.length || parts.every((p) => soundKey(choices[p.role]) === 'encoded')) return 'encoded';
  const programs = new Set(parts.map((p) => soundProgram(p, choices[p.role])));
  if (programs.size !== 1) return 'mixed';
  return Object.keys(SOUND_CHOICES).find((key) => SOUND_CHOICES[key].program === [...programs][0]) || 'encoded';
}
