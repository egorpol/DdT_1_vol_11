#!/usr/bin/env python3
"""List musical suspects in the assembled works for triage against DdT.

Every row is a suspect, not an error: check it on the printed page before
changing anything, and never change notation only to silence a row.

Checks: duplicate pitches in a chord, unisons with a cross-staff note, notes
outside generous role ranges, isolated octave leaps, same-letter notes with
different accidentals struck together in different voices, figure accidentals
that no sounding note honours, figures over silence or with doubtful text,
tstamps past the barline, ties between different pitches, notes without pitch,
and event IDs present in the baseline tag but missing now. Known idioms are
left out: octave returns, figures over a held bass, clashes between a held
and a moving note.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

# CAMAT's resolver carries written accidentals to the barline and applies key signatures.
from camat.verovio_backend import _extract_mei_note_effective_alters

ROOT = Path(__file__).resolve().parents[1]
MEI = '{http://www.music-encoding.org/ns/mei}'
ID = '{http://www.w3.org/XML/1998/namespace}id'
STEPS = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}
LETTERS = 'cdefgab'
DURATIONS = {'long': Fraction(16), 'breve': Fraction(8), '1': Fraction(4), '2': Fraction(2), '4': Fraction(1),
             '8': Fraction(1, 2), '16': Fraction(1, 4), '32': Fraction(1, 8), '64': Fraction(1, 16)}
# Generous MIDI bounds per staff role; a note outside them is a likely octave slip.
RANGES = {'violin': (55, 88), 'violin_1': (55, 88), 'violin_2': (55, 88),
          'viola_da_gamba': (33, 79), 'violone': (28, 67), 'figured_continuo_bass': (31, 67),
          'keyboard_realization_upper': (45, 88), 'keyboard_realization_lower': (31, 72)}
CONTROL = {'harm', 'dir', 'dynam', 'tempo', 'fermata', 'trill', 'mordent', 'turn', 'hairpin', 'slur', 'tie', 'arpeg'}
FIGURE_ACCIDENTALS = {'♯': 1, '#': 1, '♭': -1, 'b': -1, '♮': 0}
# Semitones of the major or perfect interval per figure; ♯/♭ on a perfect one mean augmented/diminished.
MAJOR = {2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11, 8: 12, 9: 14}
PERFECT = {4, 5, 8}


def local(tag):
    return tag.rsplit('}', 1)[-1]


def duration(element):
    base = DURATIONS.get(element.get('dur', ''))
    if base is None:
        return None
    dots = int(element.get('dots', '0'))
    return base * (2 - Fraction(1, 2 ** dots))


def key_alters(sig):
    match = re.fullmatch(r'([0-7])([sf]?)', sig or '')
    if not match:
        return None
    letters = 'fcgdaeb' if match[2] == 's' else 'beadgcf'
    return {letter: (1 if match[2] == 's' else -1) for letter in letters[:int(match[1])]}


class Work:
    def __init__(self, entry):
        self.key = entry['key']
        self.file = entry['file']
        self.roles = entry.get('staff_roles', {})
        self.root = ET.parse(ROOT / self.file).getroot()
        self.alters = _extract_mei_note_effective_alters(self.root)
        self.notes = []      # dicts: id, el, measure, staff, layer, onset, end, midi, pname, oct, alter, chord
        self.measures = []   # (measure element, meter count, meter unit, key per staff, page)
        self.sequence = defaultdict(int)  # events so far per (staff, layer); rests count too
        self.unpitched = []  # (note, measure, staff) lacking @pname or @oct
        self.timeline()

    def timeline(self):
        count, unit, keys, page = 4, 4, defaultdict(dict), ''
        for element in self.root.find(MEI + 'music').iter():
            tag = local(element.tag)
            if tag in {'scoreDef', 'staffDef'}:
                meter = element.find(MEI + 'meterSig')
                for source in (element, meter):
                    if source is not None and (source.get('meter.count') or source.get('count')):
                        count = int(source.get('meter.count') or source.get('count'))
                        unit = int(source.get('meter.unit') or source.get('unit'))
                for definition in ([element] if tag == 'staffDef' else element.iter(MEI + 'staffDef')):
                    signature = definition.find(MEI + 'keySig')
                    if signature is not None and key_alters(signature.get('sig')) is not None:
                        keys[definition.get('n')] = key_alters(signature.get('sig'))
                if tag == 'scoreDef':
                    signature = element.find(MEI + 'keySig')
                    if signature is not None and key_alters(signature.get('sig')) is not None:
                        for staff in list(keys) or [str(n) for n in range(1, 7)]:
                            keys[staff] = key_alters(signature.get('sig'))
            elif tag == 'pb':
                page = element.get('n', '')
            elif tag == 'measure':
                self.measures.append((element, count, unit, {n: dict(k) for n, k in keys.items()}, page))
                length = Fraction(count * 4, unit)
                for staff in element.findall(MEI + 'staff'):
                    for layer in staff.findall(MEI + 'layer'):
                        self.walk(layer, Fraction(0), Fraction(1), element, staff.get('n'), layer.get('n'), length)

    def walk(self, parent, onset, scale, measure, staff, layer, length):
        for child in parent:
            tag = local(child.tag)
            if tag in {'beam'}:
                onset = self.walk(child, onset, scale, measure, staff, layer, length)
            elif tag == 'tuplet':
                ratio = Fraction(int(child.get('numbase')), int(child.get('num')))
                onset = self.walk(child, onset, scale * ratio, measure, staff, layer, length)
            elif tag in {'note', 'chord', 'rest', 'space', 'mRest', 'mSpace'}:
                self.sequence[(staff, layer)] += 1
            if tag in {'note', 'chord'}:
                notes = [child] if tag == 'note' else child.findall(MEI + 'note')
                span = (duration(child) or max((duration(n) or 0 for n in notes), default=0)) * scale
                for note in notes:
                    if note.get('pname') not in STEPS or not (note.get('oct') or '').lstrip('-').isdigit():
                        self.unpitched.append((note, measure, note.get('staff') or staff))
                        continue
                    pname, octave = note.get('pname'), int(note.get('oct'))
                    alter = self.alters.get(id(note), 0)
                    self.notes.append({
                        'id': note.get(ID, ''), 'el': note, 'measure': measure,
                        'staff': note.get('staff') or child.get('staff') or staff, 'layer': layer,
                        'onset': onset, 'end': onset + span, 'pname': pname, 'oct': octave, 'alter': alter,
                        'midi': 12 * (octave + 1) + STEPS[pname] + alter,
                        'chord': child if tag == 'chord' else None, 'seq': self.sequence[(staff, layer)]})
                onset += span
            elif tag in {'rest', 'space'}:
                onset += (duration(child) or 0) * scale
            elif tag in {'mRest', 'mSpace'}:
                onset += length
        return onset


def tstamp_onset(value, unit):
    return (Fraction(value) - 1) * Fraction(4, unit)


def spelled(note):
    return note['pname'].upper() + {-2: 'bb', -1: 'b', 0: '', 1: '#', 2: 'x'}.get(note['alter'], '?') + str(note['oct'])


def lint(work):
    rows = []
    measure_info = {m.get(ID): (m, count, unit, keys, page) for m, count, unit, keys, page in work.measures}

    def add(check, measure, staff, ids, detail):
        rows.append({'work': work.key, 'page': measure_info[measure.get(ID)][4], 'measure': measure.get('n'),
                     'zone': measure.get('facs', '').removeprefix('#'), 'staff': staff, 'role': work.roles.get(staff, ''), 'check': check,
                     'xml_ids': ' '.join(ids), 'detail': detail})

    by_measure = defaultdict(list)
    for note in work.notes:
        by_measure[note['measure'].get(ID)].append(note)
    by_id = {note['id']: note for note in work.notes if note['id']}

    chords = defaultdict(list)
    for note in work.notes:
        if note['chord'] is not None:
            chords[id(note['chord'])].append(note)
    for members in chords.values():
        seen = Counter((n['pname'], n['oct']) for n in members)
        for (pname, octave), number in seen.items():
            if number > 1:
                same = [n for n in members if (n['pname'], n['oct']) == (pname, octave)]
                add('chord_duplicate_pitch', same[0]['measure'], same[0]['staff'], [n['id'] for n in same],
                    f'{number}× {spelled(same[0])} in one chord ({" ".join(spelled(n) for n in members)})')

    for key, notes in by_measure.items():
        measure, count, unit, keys, _ = measure_info[key]
        notes.sort(key=lambda n: (n['onset'], n['staff'], n['layer']))
        clashes = defaultdict(dict)
        for i, a in enumerate(notes):
            for b in notes[i + 1:]:
                if b['onset'] >= a['end']:
                    continue
                cross = any(n['el'].get('staff') or (n['chord'] is not None and n['chord'].get('staff')) for n in (a, b))
                if a['staff'] == b['staff'] and a['onset'] == b['onset'] and a['midi'] == b['midi'] and cross:
                    add('same_staff_unison', measure, a['staff'], [a['id'], b['id']],
                        f'{spelled(a)} twice on staff {a["staff"]} at beat {float(a["onset"] * unit / 4 + 1):g} '
                        f'(layers {a["layer"]}/{b["layer"]})')
                if a['pname'] == b['pname'] and a['alter'] != b['alter'] and a['onset'] == b['onset'] \
                        and (a['staff'], a['layer']) != (b['staff'], b['layer']):
                    clashes[(a['onset'], a['pname'])].update({id(a): a, id(b): b})
        for (onset, pname), group in clashes.items():
            members = sorted(group.values(), key=lambda n: n['staff'])
            add('accidental_clash', measure, '+'.join(sorted({n['staff'] for n in members})), [n['id'] for n in members],
                f'struck together at beat {float(onset * unit / 4 + 1):g}: '
                + ', '.join(f'{spelled(n)} (staff {n["staff"]})' for n in members))

    for staff, role in work.roles.items():
        low, high = RANGES.get(role, (0, 127))
        for note in work.notes:
            if note['staff'] == staff and not low <= note['midi'] <= high:
                add('out_of_range', note['measure'], staff, [note['id']],
                    f'{spelled(note)} (MIDI {note["midi"]}) outside {role} bounds {low}–{high}')

    lines = defaultdict(list)
    for note in work.notes:
        if note['chord'] is None and note['el'].get('staff') is None:
            lines[(note['staff'], note['layer'])].append(note)
    for (staff, layer), line in lines.items():
        order = sorted(line, key=lambda n: n['seq'])
        for a, b, c in zip(order, order[1:], order[2:]):
            if (b['seq'] - a['seq'], c['seq'] - b['seq']) != (1, 1):
                continue  # a rest or a chord separates the notes
            up, down = b['midi'] - a['midi'], c['midi'] - b['midi']
            octave_return = abs(up) == abs(down) == 12 and a['midi'] == c['midi']
            if abs(up) >= 10 and abs(down) >= 10 and up * down < 0 and abs(c['midi'] - a['midi']) <= 2 and not octave_return:
                add('octave_displacement', b['measure'], staff, [b['id']],
                    f'{spelled(a)} → {spelled(b)} → {spelled(c)}: isolated leap of {up:+d}/{down:+d} semitones')

    for measure, count, unit, keys, _ in work.measures:
        notes = by_measure[measure.get(ID)]
        for event in measure:
            tag = local(event.tag)
            if tag not in CONTROL or not event.get('tstamp'):
                continue
            stamp = Fraction(event.get('tstamp'))
            if stamp >= count + 1 or stamp < 0:
                add('tstamp_beyond_bar', measure, event.get('staff', ''), [event.get(ID, '')],
                    f'{tag} at tstamp {event.get("tstamp")} in a {count}/{unit} bar')
        for harm in measure.findall(MEI + 'harm'):
            staff, onset = harm.get('staff'), tstamp_onset(harm.get('tstamp') or '1', unit)
            bass = [n for n in notes if n['staff'] == staff and n['onset'] <= onset < n['end']]
            figures = [''.join(f.itertext()).strip() for f in harm.iter(MEI + 'f')]
            if not bass:  # figures over a held bass note are normal
                add('figure_over_silence', measure, staff, [harm.get(ID, '')],
                    f'figures {figures} at tstamp {harm.get("tstamp")}: no note sounds there on staff {staff}')
            for figure in figures:
                if not figure or '?' in figure or re.search(r'[^0-9♯♭♮#b() +\-/]', figure):
                    add('figure_text', measure, staff, [harm.get(ID, '')], f'figure text {figure!r}')
            if not bass:
                continue
            low = min(bass, key=lambda n: n['midi'])
            for figure in figures:
                for number, accidental in re.findall(r'(\d*)\s*([♯#♭b♮])', figure.replace('(', '').replace(')', '')):
                    interval = int(number or 3)
                    letter = LETTERS[(LETTERS.index(low['pname']) + interval - 1) % 7]
                    base = keys.get(staff, {}).get(letter, 0)
                    expected = 0 if accidental == '♮' else base + FIGURE_ACCIDENTALS[accidental]
                    # Old figures may instead name the interval's quality (5♭ over B♮ = F♮, a diminished fifth).
                    size = MAJOR.get(interval if interval < 10 else interval - 7)
                    quality = None if size is None or accidental == '♮' else \
                        size + (FIGURE_ACCIDENTALS[accidental] if size in {MAJOR[k] for k in PERFECT} else min(FIGURE_ACCIDENTALS[accidental], 0))
                    sounding = [n for n in notes if n['pname'] == letter and n['onset'] <= onset < n['end']
                                and n['staff'] != staff]
                    wrong = [n for n in sounding if n['alter'] != expected
                             and (quality is None or (n['midi'] - low['midi']) % 12 != quality % 12)]
                    if wrong:
                        add('figure_accidental_conflict', measure, staff, [harm.get(ID, '')] + [n['id'] for n in wrong],
                            f'figure {figure!r} over {spelled(low)} asks {letter.upper()}'
                            f'{ {-1: "b", 0: "", 1: "#"}.get(expected, "?") }; sounding: '
                            + ', '.join(f'{spelled(n)} (staff {n["staff"]})' for n in wrong))

    for note, measure, staff in work.unpitched:
        add('missing_pitch', measure, staff, [note.get(ID, '')],
            f'note with pname={note.get("pname")!r} oct={note.get("oct")!r}')

    for tie in work.root.iter(MEI + 'tie'):
        start, end = (by_id.get(tie.get(k, '').removeprefix('#')) for k in ('startid', 'endid'))
        if start and end and start['midi'] != end['midi']:
            add('tie_pitch_mismatch', start['measure'], start['staff'], [tie.get(ID, ''), start['id'], end['id']],
                f'tie joins {spelled(start)} to {spelled(end)}')
    return rows


def id_churn(work, tag, events):
    try:
        old = subprocess.run(['git', '-C', str(ROOT), 'show', f'{tag}:{work.file}'], capture_output=True, check=True).stdout
    except subprocess.CalledProcessError:
        return []
    old_root = ET.fromstring(old)
    now = {e.get(ID) for e in work.root.iter() if e.get(ID)}
    rows = []
    for element in old_root.find(MEI + 'music').iter():
        if local(element.tag) in events and element.get(ID) and element.get(ID) not in now:
            rows.append({'work': work.key, 'page': '', 'measure': '', 'zone': '', 'staff': element.get('staff', ''), 'role': '',
                         'check': 'event_id_removed', 'xml_ids': element.get(ID),
                         'detail': f'{local(element.tag)} present in {tag}, missing now'})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--manifest', default='validation/editorial-works.json')
    parser.add_argument('--baseline-tag', default='v0.9.0')
    parser.add_argument('--work', action='append', help='limit to work keys')
    parser.add_argument('--out', default='validation/runs/musical-lint/suspects.csv')
    args = parser.parse_args()
    events = set(json.loads((ROOT / 'validation/profile.json').read_text())['event_elements'])
    rows = []
    for entry in json.loads((ROOT / args.manifest).read_text())['works']:
        if args.work and entry['key'] not in args.work:
            continue
        work = Work(entry)
        rows += lint(work) + id_churn(work, args.baseline_tag, events)
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['work', 'page', 'measure', 'zone', 'staff', 'role', 'check', 'xml_ids', 'detail'])
        writer.writeheader()
        writer.writerows(rows)
    for (check,), number in sorted(Counter((r['check'],) for r in rows).items()):
        print(f'{number:6d}  {check}')
    print(f'{len(rows)} suspects -> {out.relative_to(ROOT)}')


if __name__ == '__main__':
    sys.exit(main())
