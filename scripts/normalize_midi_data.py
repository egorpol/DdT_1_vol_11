#!/usr/bin/env python3
"""Set MIDI instruments and channels on the assembled works; drop OMR tempo values.

Editor's decision (2026-10-27, refined 2026-10-28): each part gets a General
MIDI program from the staff's role in validation/editorial-works.json, written
as @midi.instrnum (0-based) only — not @midi.instrname (MEI Schematron allows
only one of the two, and Verovio 6.3.0 reads the number). Any midi.instrname
on an instrDef is removed. Parts in score order: every staff whose role is not
keyboard_realization_* is one part; the two realization staves share one part
(their <instrDef> sits on the brace <staffGrp>). Channels count 0, 1, 2 …
skipping 9 (GM percussion). Remove every @midi.bpm and @midi.mspb from any
element (scoreDef, staffDef, tempo, …) and every @mm / @mm.unit / @mm.dots
from <tempo>; keep the elements, text and other attributes. Start tags may
span lines. Figured bass and realization both sound. Edits are text-level
on UTF-8 bytes so the rest of each file stays byte-identical, including CRLF.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEI = '{http://www.music-encoding.org/ns/mei}'
ID = '{http://www.w3.org/XML/1998/namespace}id'

ROLE_PROGRAM = {
    'violin': (40, 'Violin'),
    'violin_1': (40, 'Violin'),
    'violin_2': (40, 'Violin'),
    'viola_da_gamba': (42, 'Cello'),
    'violone': (43, 'Contrabass'),
    'figured_continuo_bass': (6, 'Harpsichord'),
    'keyboard_realization_upper': (6, 'Harpsichord'),
    'keyboard_realization_lower': (6, 'Harpsichord'),
}
REALIZATION_ROLES = frozenset({
    'keyboard_realization_upper',
    'keyboard_realization_lower',
})

RATE_DROP_ATTRS = frozenset({'midi.bpm', 'midi.mspb'})
TEMPO_DROP_ATTRS = frozenset({'mm', 'mm.unit', 'mm.dots'})
INSTR_DROP_ATTRS = frozenset({'midi.instrname'})


def local(tag):
    return tag.rsplit('}', 1)[-1]


def local_element_name(name):
    return name.rsplit(':', 1)[-1]


def read_work_text(path):
    return path.read_bytes().decode('utf-8')


def write_work_text(path, text):
    path.write_bytes(text.encode('utf-8'))


def apply_span_edits(text, edits):
    """Apply (start, end, replacement) spans; raise if any two overlap."""
    ordered = sorted(edits, key=lambda e: (e[0], e[1]))
    prev_end = -1
    for start, end, _replacement in ordered:
        if start < 0 or end < start or end > len(text):
            raise ValueError(f'invalid edit span {start}:{end} (len={len(text)})')
        if start < prev_end:
            raise ValueError(
                f'overlapping edits: previous ends at {prev_end}, next is {start}:{end}'
            )
        prev_end = end
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


def midi_channels(n_parts):
    """Assign MIDI channels 0, 1, 2 … skipping 9 (GM percussion)."""
    channels = []
    ch = 0
    while len(channels) < n_parts:
        if ch != 9:
            channels.append(ch)
        ch += 1
        if ch > 15 and len(channels) < n_parts:
            raise ValueError(f'need {n_parts} channels but only 15 non-percussion MIDI channels exist')
    return channels


def build_parts(staff_roles):
    """Return (parts, staff_to_part) from staff_roles keyed by staff @n string.

    parts: list of dicts with keys staff_ns, role (representative), channel,
    instrnum, instrname. Realization staves share one part.
    """
    ordered = sorted(staff_roles.items(), key=lambda kv: int(kv[0]))
    parts = []
    staff_to_part = {}
    realization_part = None
    for n, role in ordered:
        if role not in ROLE_PROGRAM:
            raise ValueError(f'unknown role {role!r} for staff {n}')
        if role in REALIZATION_ROLES:
            if realization_part is None:
                instrnum, instrname = ROLE_PROGRAM[role]
                realization_part = {
                    'staff_ns': [n],
                    'role': role,
                    'instrnum': instrnum,
                    'instrname': instrname,
                }
                parts.append(realization_part)
            else:
                if ROLE_PROGRAM[role] != (
                    realization_part['instrnum'],
                    realization_part['instrname'],
                ):
                    raise ValueError(
                        f'realization roles disagree: {realization_part["role"]} vs {role}'
                    )
                realization_part['staff_ns'].append(n)
            staff_to_part[n] = realization_part
        else:
            instrnum, instrname = ROLE_PROGRAM[role]
            part = {
                'staff_ns': [n],
                'role': role,
                'instrnum': instrnum,
                'instrname': instrname,
            }
            parts.append(part)
            staff_to_part[n] = part
    channels = midi_channels(len(parts))
    for part, channel in zip(parts, channels):
        part['channel'] = channel
    return parts, staff_to_part


def parent_map(root):
    return {child: parent for parent in root.iter() for child in parent}


def opening_score_def(root):
    score = next(root.iter(MEI + 'score'), None)
    if score is None:
        raise ValueError('no <score>')
    for child in score.iter():
        if local(child.tag) == 'scoreDef':
            return child
    raise ValueError('no <scoreDef> under <score>')


def classify_instr_defs(entry, root, parts, staff_to_part, staff_roles):
    """Map each instrDef xml:id to its expected part (channel, instrnum).

    Validates placement rules and that every part has an instrDef in the
    opening scoreDef.
    """
    parents = parent_map(root)
    expected = {}
    opening = opening_score_def(root)
    opening_parts_seen = set()

    # Every staffDef and every sounding <staff> must have a known role.
    for staff_def in root.iter(MEI + 'staffDef'):
        n = staff_def.get('n')
        if n is None:
            continue
        if n not in staff_roles:
            raise ValueError(
                f'{entry["file"]}: staffDef n={n!r} has no role in staff_roles'
            )
    for staff in root.iter(MEI + 'staff'):
        n = staff.get('n')
        if n is None:
            continue
        if n not in staff_roles:
            raise ValueError(
                f'{entry["file"]}: staff n={n!r} has no role in staff_roles'
            )

    for instr in root.iter(MEI + 'instrDef'):
        iid = instr.get(ID)
        if not iid:
            raise ValueError(f'{entry["file"]}: <instrDef> without xml:id')
        parent = parents[instr]
        ptag = local(parent.tag)

        if ptag == 'staffDef':
            n = parent.get('n')
            if n is None:
                raise ValueError(
                    f'{entry["file"]}: instrDef {iid!r} in staffDef without @n'
                )
            role = staff_roles[n]
            if role in REALIZATION_ROLES:
                raise ValueError(
                    f'{entry["file"]}: instrDef {iid!r} sits in realization '
                    f'staffDef n={n} (role {role}); expected on the brace staffGrp'
                )
            part = staff_to_part[n]
            expected[iid] = part
            if _element_is_under(instr, opening, parents):
                opening_parts_seen.add(id(part))
        elif ptag == 'staffGrp':
            # Every descendant staffDef counts, including those in nested groups.
            child_defs = list(parent.iter(MEI + 'staffDef'))
            if not child_defs:
                raise ValueError(
                    f'{entry["file"]}: instrDef {iid!r} on staffGrp with no staffDefs'
                )
            staff_ns = []
            for sd in child_defs:
                n = sd.get('n')
                if n is None or n not in staff_roles:
                    raise ValueError(
                        f'{entry["file"]}: staffDef under instrDef {iid!r} '
                        f'has no role (n={n!r})'
                    )
                role = staff_roles[n]
                if role not in REALIZATION_ROLES:
                    raise ValueError(
                        f'{entry["file"]}: instrDef {iid!r} on staffGrp whose '
                        f'descendant staffDef n={n} is not a realization staff'
                    )
                staff_ns.append(n)
            part = staff_to_part[staff_ns[0]]
            if set(staff_ns) != set(part['staff_ns']):
                expected_ns = set(part['staff_ns'])
                offending = next(
                    (n for n in staff_ns if n not in expected_ns),
                    next(n for n in sorted(expected_ns, key=int) if n not in staff_ns),
                )
                raise ValueError(
                    f'{entry["file"]}: instrDef {iid!r} on staffGrp does not '
                    f'cover exactly the realization part (offending staff n={offending})'
                )
            expected[iid] = part
            if _element_is_under(instr, opening, parents):
                opening_parts_seen.add(id(part))
        else:
            raise ValueError(
                f'{entry["file"]}: instrDef {iid!r} under unexpected <{ptag}>'
            )

    for part in parts:
        if id(part) not in opening_parts_seen:
            raise ValueError(
                f'{entry["file"]}: part for staff(s) {part["staff_ns"]} '
                f'(role {part["role"]}) has no instrDef in the opening scoreDef'
            )
    return expected


def _element_is_under(element, ancestor, parents):
    cur = element
    while cur in parents:
        cur = parents[cur]
        if cur is ancestor:
            return True
    return False


def _skip_doctype(text, start, source='<input>'):
    """Return index after a plain <!DOCTYPE …>; refuse internal DTD subsets.

    Quoted SYSTEM/PUBLIC literals may contain '>'; a '[' before the closing
    '>' means an internal subset, which this scanner does not support.
    """
    i = start + len('<!DOCTYPE')
    while i < len(text):
        ch = text[i]
        if ch in '"\'':
            quote = ch
            i += 1
            while i < len(text) and text[i] != quote:
                i += 1
            if i >= len(text):
                raise ValueError(f'{source}: unclosed quote in <!DOCTYPE>')
            i += 1
            continue
        if ch == '[':
            raise ValueError(
                f'{source}: internal DTD subsets are not supported'
            )
        if ch == '>':
            return i + 1
        i += 1
    raise ValueError(f'{source}: unclosed <!DOCTYPE>')


def iter_markup_start_tags(text, source='<input>'):
    """Yield (start, end, element_name, tag) for real start tags; skip comments etc."""
    i = 0
    n = len(text)
    while i < n:
        lt = text.find('<', i)
        if lt < 0:
            return
        if text.startswith('<!--', lt):
            end = text.find('-->', lt + 4)
            if end < 0:
                raise ValueError(f'{source}: unclosed comment at {lt}')
            i = end + 3
            continue
        if text.startswith('<![CDATA[', lt):
            end = text.find(']]>', lt + 9)
            if end < 0:
                raise ValueError(f'{source}: unclosed CDATA at {lt}')
            i = end + 3
            continue
        if text.startswith('<?', lt):
            end = text.find('?>', lt + 2)
            if end < 0:
                raise ValueError(f'{source}: unclosed processing instruction at {lt}')
            i = end + 2
            continue
        if text.startswith('<!DOCTYPE', lt) or text.startswith('<!doctype', lt):
            i = _skip_doctype(text, lt, source=source)
            continue
        if text.startswith('<!', lt):
            end = text.find('>', lt + 2)
            if end < 0:
                raise ValueError(f'{source}: unclosed declaration at {lt}')
            i = end + 1
            continue
        if text.startswith('</', lt):
            end = text.find('>', lt + 2)
            if end < 0:
                raise ValueError(f'{source}: unclosed end tag at {lt}')
            i = end + 1
            continue
        # Element start tag: attribute values never contain '<' or '>'.
        end = text.find('>', lt + 1)
        if end < 0:
            raise ValueError(f'{source}: unclosed start tag at {lt}')
        tag = text[lt:end + 1]
        name_end = 1
        while name_end < len(tag) - 1 and not tag[name_end].isspace() and tag[name_end] not in '/>':
            name_end += 1
        name = tag[1:name_end]
        if not name or not (name[0].isalpha() or name[0] == '_'):
            i = end + 1
            continue
        yield lt, end + 1, name, tag
        i = end + 1


class AttrToken:
    __slots__ = ('leading_ws', 'name', 'eq_prefix', 'eq_suffix', 'quote', 'value')

    def __init__(self, leading_ws, name, eq_prefix, eq_suffix, quote, value):
        self.leading_ws = leading_ws
        self.name = name
        self.eq_prefix = eq_prefix
        self.eq_suffix = eq_suffix
        self.quote = quote
        self.value = value

    def copy(self, **kwargs):
        return AttrToken(
            kwargs.get('leading_ws', self.leading_ws),
            kwargs.get('name', self.name),
            kwargs.get('eq_prefix', self.eq_prefix),
            kwargs.get('eq_suffix', self.eq_suffix),
            kwargs.get('quote', self.quote),
            kwargs.get('value', self.value),
        )

    def render(self):
        return (
            f'{self.leading_ws}{self.name}{self.eq_prefix}='
            f'{self.eq_suffix}{self.quote}{self.value}{self.quote}'
        )


def parse_start_tag(tag):
    """Parse a start tag into name, attribute tokens, self-closing flag, trailing ws."""
    if not (tag.startswith('<') and tag.endswith('>')):
        raise ValueError(f'not a start tag: {tag!r}')
    body = tag[1:-1]
    self_closing = False
    if body.endswith('/'):
        self_closing = True
        body = body[:-1]
    i = 0
    while i < len(body) and not body[i].isspace() and body[i] not in '/>':
        i += 1
    name = body[:i]
    attrs = []
    while i < len(body):
        ws_start = i
        while i < len(body) and body[i].isspace():
            i += 1
        leading_ws = body[ws_start:i]
        if i >= len(body):
            return name, attrs, self_closing, leading_ws
        name_start = i
        while i < len(body) and not body[i].isspace() and body[i] != '=':
            i += 1
        attr_name = body[name_start:i]
        eq_prefix_start = i
        while i < len(body) and body[i].isspace():
            i += 1
        eq_prefix = body[eq_prefix_start:i]
        if i >= len(body) or body[i] != '=':
            raise ValueError(f'missing = after attribute {attr_name!r} in {tag!r}')
        i += 1
        eq_suffix_start = i
        while i < len(body) and body[i].isspace():
            i += 1
        eq_suffix = body[eq_suffix_start:i]
        if i >= len(body) or body[i] not in '"\'':
            raise ValueError(f'missing quoted value for {attr_name!r} in {tag!r}')
        quote = body[i]
        i += 1
        val_start = i
        while i < len(body) and body[i] != quote:
            i += 1
        if i >= len(body):
            raise ValueError(f'unclosed quote for {attr_name!r} in {tag!r}')
        value = body[val_start:i]
        i += 1
        attrs.append(AttrToken(leading_ws, attr_name, eq_prefix, eq_suffix, quote, value))
    return name, attrs, self_closing, ''


def serialize_start_tag(name, attrs, self_closing, trailing_ws):
    parts = ['<', name]
    for attr in attrs:
        parts.append(attr.render())
    parts.append(trailing_ws)
    if self_closing:
        parts.append('/>')
    else:
        parts.append('>')
    return ''.join(parts)


def attr_map(attrs):
    return {a.name: a.value for a in attrs}


def rewrite_start_tag(tag, instr_target=None):
    """One replacement for a start tag: instrDef channel/program + drop rate/name attrs.

    instr_target: (channel, instrnum) for <instrDef>, else None.
    Returns (patched_tag, dropped_attr_names).
    """
    name, attrs, self_closing, trailing_ws = parse_start_tag(tag)
    el = local_element_name(name)
    drop = set(RATE_DROP_ATTRS)
    if el == 'tempo':
        drop |= TEMPO_DROP_ATTRS
    if el == 'instrDef' or instr_target is not None:
        drop |= INSTR_DROP_ATTRS

    dropped = []
    new_attrs = []
    for attr in attrs:
        if attr.name in drop:
            dropped.append(attr.name)
            continue
        if instr_target is not None and attr.name == 'midi.channel':
            new_attrs.append(attr.copy(value=str(instr_target[0])))
        elif instr_target is not None and attr.name == 'midi.instrnum':
            new_attrs.append(attr.copy(value=str(instr_target[1])))
        else:
            new_attrs.append(attr)

    if instr_target is not None:
        present = {a.name for a in new_attrs}
        channel, instrnum = instr_target
        if 'midi.channel' not in present:
            new_attrs.append(AttrToken(' ', 'midi.channel', '', '', '"', str(channel)))
        if 'midi.instrnum' not in present:
            new_attrs.append(AttrToken(' ', 'midi.instrnum', '', '', '"', str(instrnum)))

    return serialize_start_tag(name, new_attrs, self_closing, trailing_ws), dropped


def current_instr_values(tag):
    """Return (channel, instrnum, instrname_or_None). Name must be absent."""
    _name, attrs, _sc, _tw = parse_start_tag(tag)
    values = attr_map(attrs)
    return (
        values.get('midi.channel'),
        values.get('midi.instrnum'),
        values.get('midi.instrname'),
    )


def plan_work(entry):
    path = ROOT / entry['file']
    text = read_work_text(path)
    staff_roles = {str(k): v for k, v in entry['staff_roles'].items()}
    parts, staff_to_part = build_parts(staff_roles)
    root = ET.fromstring(text.encode('utf-8'))
    expected = classify_instr_defs(entry, root, parts, staff_to_part, staff_roles)

    edits = []
    instr_diffs = []
    rate_diffs = []
    seen_instr_ids = set()

    for start, end, name, tag in iter_markup_start_tags(text, source=entry['file']):
        el = local_element_name(name)
        instr_target = None
        part = None
        iid = None
        if el == 'instrDef':
            iid = attr_map(parse_start_tag(tag)[1]).get('xml:id')
            if iid in expected:
                part = expected[iid]
                instr_target = (part['channel'], part['instrnum'])
                seen_instr_ids.add(iid)

        patched, dropped = rewrite_start_tag(tag, instr_target=instr_target)

        if part is not None:
            current = current_instr_values(tag)
            target = (str(part['channel']), str(part['instrnum']), None)
            if current != target:
                instr_diffs.append({
                    'id': iid,
                    'current': current,
                    'target': target,
                    'part': part,
                })

        if dropped:
            rate_diffs.append({
                'element': el,
                'tag': tag,
                'start': start,
                'end': end,
                'patched': patched,
                'dropped': dropped,
            })

        if patched != tag:
            edits.append((start, end, patched))

    missing = set(expected) - seen_instr_ids
    if missing:
        raise ValueError(
            f'{entry["file"]}: instrDef xml:id(s) not found in markup: '
            f'{", ".join(sorted(missing))}'
        )

    return {
        'text': text,
        'path': path,
        'parts': parts,
        'expected': expected,
        'edits': edits,
        'instr_diffs': instr_diffs,
        'rate_diffs': rate_diffs,
    }


def check_work(entry):
    plan = plan_work(entry)
    return plan['instr_diffs'], plan['rate_diffs']


def write_work(entry):
    plan = plan_work(entry)
    bpm_removed = mspb_removed = mm_removed = 0
    for diff in plan['rate_diffs']:
        if 'midi.bpm' in diff['dropped']:
            bpm_removed += 1
        if 'midi.mspb' in diff['dropped']:
            mspb_removed += 1
        if 'mm' in diff['dropped']:
            mm_removed += 1

    text = apply_span_edits(plan['text'], plan['edits'])
    write_work_text(plan['path'], text)
    return {
        'instr_defs_changed': len(plan['instr_diffs']),
        'instr_defs_total': len(plan['expected']),
        'rate_marks': len(plan['rate_diffs']),
        'midi_bpm_removed': bpm_removed,
        'midi_mspb_removed': mspb_removed,
        'mm_removed': mm_removed,
        'parts': plan['parts'],
    }


def format_instr_diff(entry_key, diff):
    cur_ch, cur_num, cur_name = diff['current']
    tgt_ch, tgt_num, _ = diff['target']
    label = diff['part']['instrname']
    cur = f'channel {cur_ch} program {cur_num}'
    if cur_name is not None:
        cur += f' instrname={cur_name}'
    return (
        f"{entry_key} instrDef {diff['id']}: "
        f"current={cur} "
        f"target=channel {tgt_ch} program {tgt_num} ({label})"
    )


def format_rate_diff(entry_key, diff):
    attrs = ', '.join(diff['dropped'])
    mid = re.search(r'\bxml:id="([^"]*)"', diff['tag'])
    label = f'xml:id={mid.group(1)!r}' if mid else diff['tag'][:80].replace('\n', ' ')
    return (
        f"{entry_key} <{diff['element']}> {label}: would remove {attrs}"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        '--check', action='store_true', default=None,
        help='list every instrDef/rate attr that differs from the target (default)',
    )
    mode.add_argument(
        '--write', action='store_true',
        help='edit the files in place',
    )
    parser.add_argument(
        '--work', action='append', dest='works',
        help='limit to manifest key (repeatable)',
    )
    parser.add_argument('--manifest', default='validation/editorial-works.json')
    args = parser.parse_args(argv)
    do_write = bool(args.write)
    if args.check is None and not do_write:
        do_write = False  # default --check

    entries = load_works(args.manifest, args.works)
    exit_code = 0

    if do_write:
        for entry in entries:
            try:
                result = write_work(entry)
            except ValueError as exc:
                print(exc, file=sys.stderr)
                return 1
            print(
                f"{entry['key']}: changed {result['instr_defs_changed']}/"
                f"{result['instr_defs_total']} instrDef(s); "
                f"removed midi.bpm from {result['midi_bpm_removed']}, "
                f"midi.mspb from {result['midi_mspb_removed']}, "
                f"mm from {result['mm_removed']} "
                f"({result['rate_marks']} start tag(s))"
            )
    else:
        for entry in entries:
            try:
                instr_diffs, rate_diffs = check_work(entry)
            except ValueError as exc:
                print(exc, file=sys.stderr)
                return 1
            for diff in instr_diffs:
                print(format_instr_diff(entry['key'], diff))
            for diff in rate_diffs:
                print(format_rate_diff(entry['key'], diff))
            n = len(instr_diffs) + len(rate_diffs)
            if n:
                exit_code = 1
            print(
                f"{entry['key']}: {len(instr_diffs)} instrDef difference(s), "
                f"{len(rate_diffs)} rate-attribute difference(s)"
            )

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
