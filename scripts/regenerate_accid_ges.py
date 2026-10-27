#!/usr/bin/env python3
"""Derive @accid.ges on the assembled works from CAMAT's written-notation resolution.

Verovio MIDI and music21 MEI import take sounding pitch only from a note's own
@accid or @accid.ges. CAMAT resolves pitch from the key signature, written
accidentals carried per staff/letter/octave to the barline, and ties; an
explicit @accid.ges overrides that. This script regenerates every value from
CAMAT's resolution on the text with all accid.ges removed, so a stale value
cannot contaminate a successor.

Rule: a note with no written accidental and a resolved alter of ±1 or ±2 gets
accid.ges s/f/ss/ff; every other note gets none. Exactly one location remains:
the note's <accid> child if it has one (Verovio warns when a note and its
<accid> child both carry an accidental; prefer a child that already holds the
value), else the note. Unresolved notes are left untouched. Edits are
text-level on UTF-8 bytes so the rest of each file stays byte-identical,
including CRLF line endings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from camat.check_mei_consistency import strip_accid_ges_text
from camat.verovio_backend import _extract_mei_note_effective_alters

ROOT = Path(__file__).resolve().parents[1]
MEI = '{http://www.music-encoding.org/ns/mei}'
ID = '{http://www.w3.org/XML/1998/namespace}id'
ALTER_TO_GES = {1: 's', -1: 'f', 2: 'ss', -2: 'ff'}
GES_ATTR = re.compile(r'\s+accid\.ges\s*=\s*(?:"[^"]*"|\'[^\']*\')')


def local(tag):
    return tag.rsplit('}', 1)[-1]


def has_written_accidental(note):
    if note.get('accid') is not None:
        return True
    return any(
        local(child.tag) == 'accid' and child.get('accid') is not None
        for child in note
    )


def all_ges_locations(note):
    """Every accid.ges on the note or its <accid> children, in document order."""
    locations = []
    if note.get('accid.ges') is not None:
        locations.append({'location': 'note', 'value': note.get('accid.ges'), 'child_id': None})
    for child in note:
        if local(child.tag) == 'accid' and child.get('accid.ges') is not None:
            locations.append({
                'location': 'child',
                'value': child.get('accid.ges'),
                'child_id': child.get(ID),
            })
    return locations


def target_ges(note, alter):
    if alter is None:
        return None  # caller leaves unresolved notes untouched
    if has_written_accidental(note):
        return None
    return ALTER_TO_GES.get(alter)


def plan_keep(note, locations, target):
    """Which current location to keep, or where to add the value.

    Returns (keep, add): an existing correct child; else, when the note has an
    <accid> child, that child (a note attribute beside it makes Verovio warn);
    else an existing correct note attribute, or the note.
    """
    if target is None:
        return None, None
    for loc in locations:
        if loc['location'] == 'child' and loc['value'] == target:
            return loc, None
    children = [child for child in note if local(child.tag) == 'accid']
    if children:
        return None, {'location': 'child', 'value': target, 'child_id': children[0].get(ID)}
    for loc in locations:
        if loc['location'] == 'note' and loc['value'] == target:
            return loc, None
    return None, {'location': 'note', 'value': target, 'child_id': None}


def loc_key(loc):
    return (loc['location'], loc['value'], loc.get('child_id'))


def expected_keys(keep, add):
    if keep is not None:
        return {loc_key(keep)}
    if add is not None:
        return {loc_key(add)}
    return set()


def parent_map(root):
    return {child: parent for parent in root.iter() for child in parent}


def note_measure_staff(note, parents):
    measure = staff = None
    element = note
    while element in parents:
        element = parents[element]
        tag = local(element.tag)
        if tag == 'staff' and staff is None:
            staff = element.get('n', '')
        elif tag == 'measure':
            measure = element.get('n', '')
            break
    staff = note.get('staff') or staff or ''
    return measure or '', staff


def read_work_text(path):
    return path.read_bytes().decode('utf-8')


def write_work_text(path, text):
    path.write_bytes(text.encode('utf-8'))


def start_tag_for(text, xml_id, element='note'):
    pattern = (
        r'<(' + re.escape(element) + r')\b[^<>\r\n]* xml:id="'
        + re.escape(xml_id) + r'"[^<>\r\n]*>'
    )
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        raise ValueError(f'expected one <{element}> start tag for {xml_id!r}, found {len(matches)}')
    return matches[0]


def child_accid_tag(text, note_match, child_id=None):
    """Start tag of an <accid> child that carries accid.ges."""
    if note_match.group(0).endswith('/>'):
        raise ValueError(f'note {note_match.group(0)!r} has no children')
    end = text.find('</note>', note_match.end())
    if end < 0:
        raise ValueError('missing </note>')
    body = text[note_match.end():end]
    children = list(re.finditer(r'<accid\b[^<>\r\n]*>', body))
    with_ges = [m for m in children if 'accid.ges=' in m.group(0)]
    if child_id is not None:
        with_ges = [
            m for m in with_ges
            if re.search(r'\bxml:id="' + re.escape(child_id) + r'"', m.group(0))
        ]
    if len(with_ges) != 1:
        raise ValueError(
            f'expected one child accid.ges'
            + (f' with xml:id={child_id!r}' if child_id else '')
            + f', found {len(with_ges)}'
        )
    absolute = note_match.end() + with_ges[0].start()
    return re.compile(r'<accid\b[^<>\r\n]*>').match(text, absolute)


def accid_child_tag(text, note_match, child_id):
    """Start tag of the <accid> child that receives a new accid.ges."""
    if note_match.group(0).endswith('/>'):
        raise ValueError(f'note {note_match.group(0)!r} has no children')
    end = text.find('</note>', note_match.end())
    if end < 0:
        raise ValueError('missing </note>')
    body = text[note_match.end():end]
    children = list(re.finditer(r'<accid\b[^<>\r\n]*>', body))
    if child_id is not None:
        children = [
            m for m in children
            if re.search(r'\bxml:id="' + re.escape(child_id) + r'"', m.group(0))
        ]
    if not children:
        raise ValueError(f'no <accid> child' + (f' with xml:id={child_id!r}' if child_id else ''))
    absolute = note_match.end() + children[0].start()
    return re.compile(r'<accid\b[^<>\r\n]*>').match(text, absolute)


def remove_ges_from_tag(tag):
    patched, count = GES_ATTR.subn('', tag, count=1)
    if count != 1:
        raise ValueError(f'no accid.ges in {tag!r}')
    return patched


def add_ges_to_tag(tag, value):
    if 'accid.ges=' in tag:
        raise ValueError(f'accid.ges already present in {tag!r}')
    closing = re.search(r'\s*/?>$', tag)
    if closing is None:
        raise ValueError(f'unclosed start tag {tag!r}')
    pos = closing.start()
    return tag[:pos] + f' accid.ges="{value}"' + tag[pos:]


def apply_span_edits(text, edits):
    """Apply (start, end, replacement) spans; later offsets first."""
    for start, end, replacement in sorted(edits, key=lambda e: e[0], reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def load_works(manifest, work_keys):
    entries = json.loads((ROOT / manifest).read_text())['works']
    if work_keys:
        wanted = set(work_keys)
        missing = wanted - {e['key'] for e in entries}
        if missing:
            raise SystemExit(f'unknown work key(s): {", ".join(sorted(missing))}')
        entries = [e for e in entries if e['key'] in wanted]
    return entries


def plan_work(entry):
    """Compute targets and current values for one work; keep the bare tree alive."""
    path = ROOT / entry['file']
    text = read_work_text(path)
    bare_text, _ = strip_accid_ges_text(text)
    bare_root = ET.fromstring(bare_text.encode('utf-8'))
    alters = _extract_mei_note_effective_alters(bare_root)
    # CAMAT alter on the file as it stands (for removal reports).
    full_root = ET.fromstring(text.encode('utf-8'))
    full_alters = _extract_mei_note_effective_alters(full_root)
    full_by_id = {n.get(ID): n for n in full_root.iter(MEI + 'note')}
    parents = parent_map(bare_root)

    decisions = []
    unresolved = []
    for note in bare_root.iter(MEI + 'note'):
        nid = note.get(ID)
        if not nid:
            raise ValueError(f'{entry["file"]}: note without xml:id')
        alter = alters.get(id(note))
        measure, staff = note_measure_staff(note, parents)
        current_note = full_by_id[nid]
        locations = all_ges_locations(current_note)
        primary = locations[0] if locations else {'value': None, 'location': None}
        if alter is None:
            unresolved.append({
                'work': entry['key'], 'measure': measure, 'staff': staff,
                'id': nid, 'current': primary['value'], 'location': primary.get('location'),
                'locations': locations,
            })
            continue
        target = target_ges(note, alter)
        full_alter = full_alters.get(id(current_note))
        keep, add = plan_keep(current_note, locations, target)
        decisions.append({
            'work': entry['key'], 'measure': measure, 'staff': staff,
            'id': nid, 'current': primary['value'], 'location': primary.get('location'),
            'locations': locations, 'target': target,
            'keep': keep, 'add': add,
            'alter_bare': alter, 'alter_full': full_alter,
        })
    return text, path, decisions, unresolved


def location_label(location):
    if location == 'note':
        return 'on note'
    if location == 'child':
        return 'on child <accid>'
    return 'absent'


def format_value(value):
    return '(absent)' if value is None else value


def format_locations(locations):
    if not locations:
        return f'{format_value(None)} ({location_label(None)})'
    parts = []
    for loc in locations:
        label = location_label(loc['location'])
        if loc['location'] == 'child' and loc.get('child_id'):
            label = f'on child <accid xml:id="{loc["child_id"]}">'
        parts.append(f'{loc["value"]} ({label})')
    return ' + '.join(parts)


def format_expected(keep, add):
    if keep is not None:
        return format_locations([keep])
    if add is not None:
        return format_locations([add])
    return format_locations([])


def decision_differs(decision):
    current = {loc_key(loc) for loc in decision['locations']}
    return current != expected_keys(decision['keep'], decision['add'])


def check_work(entry):
    _, _, decisions, unresolved = plan_work(entry)
    diffs = [d for d in decisions if decision_differs(d)]
    return diffs, unresolved


def write_work(entry):
    text, path, decisions, unresolved = plan_work(entry)
    kept = added = removed = 0
    removal_rows = []
    edits = []
    to_add = []

    for decision in decisions:
        if not decision_differs(decision):
            if decision['keep'] is not None:
                kept += 1
            continue

        locations = decision['locations']
        keep = decision['keep']
        note_match = start_tag_for(text, decision['id'], 'note')
        keep_key = loc_key(keep) if keep is not None else None
        for loc in locations:
            if keep_key is not None and loc_key(loc) == keep_key:
                continue
            if loc['location'] == 'note':
                tag_match = note_match
            else:
                tag_match = child_accid_tag(text, note_match, loc.get('child_id'))
            patched = remove_ges_from_tag(tag_match.group(0))
            edits.append((tag_match.start(), tag_match.end(), patched))
            removed += 1
            removal_rows.append(decision)

        if decision['add'] is not None:
            added += 1
            to_add.append(decision)
        elif keep is not None:
            kept += 1

    text = apply_span_edits(text, edits)

    add_edits = []
    for decision in to_add:
        add = decision['add']
        tag_match = start_tag_for(text, decision['id'], 'note')
        if add['location'] == 'child':
            tag_match = accid_child_tag(text, tag_match, add['child_id'])
        patched = add_ges_to_tag(tag_match.group(0), add['value'])
        add_edits.append((tag_match.start(), tag_match.end(), patched))
    text = apply_span_edits(text, add_edits)

    write_work_text(path, text)
    return {
        'kept': kept, 'added': added, 'removed': removed,
        'removals': removal_rows, 'unresolved': unresolved,
        'after': kept + added,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', default=None,
                      help='list every note whose value differs from the target (default)')
    mode.add_argument('--write', action='store_true',
                      help='edit the files in place')
    parser.add_argument('--work', action='append', dest='works',
                        help='limit to manifest key (repeatable)')
    parser.add_argument('--manifest', default='validation/editorial-works.json')
    args = parser.parse_args(argv)
    do_write = bool(args.write)
    if args.check is None and not do_write:
        do_write = False  # default --check

    entries = load_works(args.manifest, args.works)
    exit_code = 0
    unresolved_total = 0

    if do_write:
        for entry in entries:
            result = write_work(entry)
            unresolved_total += len(result['unresolved'])
            print(
                f"{entry['key']}: kept {result['kept']}, added {result['added']}, "
                f"removed {result['removed']} (after {result['after']})"
            )
            for row in result['removals']:
                print(
                    f"  removed {row['id']}: CAMAT alter {row['alter_full']} -> {row['alter_bare']}"
                )
            for row in result['unresolved']:
                print(
                    f"  unresolved {row['id']} m{row['measure']} staff {row['staff']} "
                    f"current={format_locations(row['locations'])}"
                )
    else:
        for entry in entries:
            diffs, unresolved = check_work(entry)
            unresolved_total += len(unresolved)
            for row in diffs:
                print(
                    f"{row['work']} measure {row['measure']} staff {row['staff']} "
                    f"note {row['id']}: current={format_locations(row['locations'])} "
                    f"target={format_expected(row['keep'], row['add'])}"
                )
            for row in unresolved:
                print(
                    f"{row['work']} measure {row['measure']} staff {row['staff']} "
                    f"note {row['id']}: unresolved, left "
                    f"current={format_locations(row['locations'])}"
                )
            if diffs:
                exit_code = 1
            print(f"{entry['key']}: {len(diffs)} difference(s), {len(unresolved)} unresolved")

    print(f'unresolved notes: {unresolved_total}')
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
