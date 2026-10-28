"""MIDI instruments and tempo values follow the editor's 2026-10-27 decision."""
from __future__ import annotations

import base64
import importlib.util
import io
import json
import time
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import mido
import pytest
import verovio
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://www.music-encoding.org/ns/mei'
MEI = f'{{{NS}}}'
ID = '{http://www.w3.org/XML/1998/namespace}id'
FORBIDDEN_ANY = frozenset({'midi.bpm', 'midi.mspb', 'midi.instrname'})
FORBIDDEN_TEMPO = frozenset({'mm', 'mm.unit', 'mm.dots'})

# Expected GM program by staff role (editor's decision, independent of the script).
EXPECTED_PROGRAM = {
    'violin': 40,
    'violin_1': 40,
    'violin_2': 40,
    'viola_da_gamba': 42,
    'violone': 43,
    'figured_continuo_bass': 6,
    'keyboard_realization_upper': 6,
    'keyboard_realization_lower': 6,
}
REALIZATION = frozenset({
    'keyboard_realization_upper',
    'keyboard_realization_lower',
})
def expected_parts_from_roles(staff_roles):
    """Parts/channels from staff_roles without using the normalizer."""
    ordered = sorted(staff_roles.items(), key=lambda kv: int(kv[0]))
    parts = []
    staff_to_part = {}
    realization = None
    for n, role in ordered:
        program = EXPECTED_PROGRAM[role]
        if role in REALIZATION:
            if realization is None:
                realization = {'staff_ns': [n], 'program': program}
                parts.append(realization)
            else:
                realization['staff_ns'].append(n)
            staff_to_part[n] = realization
        else:
            part = {'staff_ns': [n], 'program': program}
            parts.append(part)
            staff_to_part[n] = part
    channels = []
    ch = 0
    while len(channels) < len(parts):
        if ch != 9:
            channels.append(ch)
        ch += 1
    for part, channel in zip(parts, channels):
        part['channel'] = channel
    return parts, staff_to_part


def module():
    spec = importlib.util.spec_from_file_location(
        'ddt_normalize_midi_data', ROOT / 'scripts' / 'normalize_midi_data.py'
    )
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


@pytest.fixture
def norm():
    return module()


def run_main(norm, root, argv):
    original = norm.ROOT
    norm.ROOT = root
    buf = io.StringIO()
    err = io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(err):
            code = norm.main(argv)
    finally:
        norm.ROOT = original
    return code, buf.getvalue(), err.getvalue()


def load_manifest():
    return json.loads((ROOT / 'validation' / 'editorial-works.json').read_text())


def wrap_mei(score_inner):
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<mei xmlns="{NS}">\n'
        f'<meiHead><fileDesc><titleStmt><title>fixture</title></titleStmt>'
        f'<pubStmt/></fileDesc></meiHead>\n'
        f'<music><body><mdiv><score>\n{score_inner}\n'
        f'</score></mdiv></body></music></mei>\n'
    )


def five_staff_score(instr_attrs=None, mid_score_def=None, tempo_attrs=''):
    """Minimal 5-staff opening scoreDef; optional second scoreDef and tempo."""
    defaults = {
        1: 'midi.channel="0" midi.instrnum="0" midi.volume="77%"',
        2: 'midi.channel="1" midi.instrnum="0" midi.volume="77%"',
        3: 'midi.channel="2" midi.instrnum="0" midi.volume="77%"',
        4: 'midi.channel="0" midi.instrnum="0" midi.volume="77%"',  # brace
    }
    if instr_attrs:
        defaults.update(instr_attrs)
    mid = mid_score_def or ''
    return f'''<scoreDef xml:id="sd1">
<staffGrp xml:id="outer">
<staffDef xml:id="P1" n="1" lines="5">
<instrDef xml:id="i1" {defaults[1]} />
</staffDef>
<staffDef xml:id="P2" n="2" lines="5">
<instrDef xml:id="i2" {defaults[2]} />
</staffDef>
<staffDef xml:id="P3" n="3" lines="5">
<instrDef xml:id="i3" {defaults[3]} />
</staffDef>
<staffGrp xml:id="brace">
<instrDef xml:id="i4" {defaults[4]} />
<staffDef xml:id="P4" n="4" lines="5"/>
<staffDef xml:id="P5" n="5" lines="5"/>
</staffGrp>
</staffGrp>
</scoreDef>
{mid}
<section xml:id="sec1">
<measure n="1">
<staff n="1"><layer n="1">
<note xml:id="n1" dur="4" oct="4" pname="c"/>
</layer></staff>
<tempo xml:id="t1" staff="1" tstamp="1"{tempo_attrs}>Adagio.</tempo>
</measure>
</section>'''


FIVE_ROLES = {
    '1': 'violin',
    '2': 'viola_da_gamba',
    '3': 'figured_continuo_bass',
    '4': 'keyboard_realization_upper',
    '5': 'keyboard_realization_lower',
}


def prepare(tmp_path, body, staff_roles=None, key='fixture'):
    mei = tmp_path / 'fixture_corr.mei'
    mei.write_text(wrap_mei(body), encoding='utf-8')
    (tmp_path / 'editorial-works.json').write_text(json.dumps({
        'works': [{
            'key': key,
            'file': 'fixture_corr.mei',
            'staff_roles': staff_roles or FIVE_ROLES,
        }],
    }))
    return mei


def test_corpus_normalize_check_clean(norm):
    code, out, err = run_main(norm, ROOT, ['--check'])
    assert code == 0, out + err


def test_corpus_expected_programs_and_no_tempo_values():
    """Independent of the script: programs by role; no midi.bpm/mm; tempo text kept."""
    manifest = load_manifest()
    for entry in manifest['works']:
        path = ROOT / entry['file']
        raw = path.read_bytes()
        root = etree.fromstring(raw)
        staff_roles = {str(k): v for k, v in entry['staff_roles'].items()}
        parts, staff_to_part = expected_parts_from_roles(staff_roles)

        for el in root.iter():
            if not isinstance(el.tag, str):
                continue
            attrib = el.attrib
            for name in FORBIDDEN_ANY:
                assert name not in attrib, (entry['file'], el.tag, name)
            if etree.QName(el).localname == 'tempo':
                for name in FORBIDDEN_TEMPO:
                    assert name not in attrib, (entry['file'], name)
                text_content = ''.join(el.itertext()).strip()
                assert text_content, (
                    f'{entry["file"]}: empty tempo {attrib.get(ID)!r}'
                )

        for instr in root.iter(f'{{{NS}}}instrDef'):
            parent = instr.getparent()
            ptag = etree.QName(parent).localname
            if ptag == 'staffDef':
                n = parent.get('n')
                role = staff_roles[n]
                assert role not in REALIZATION
                part = staff_to_part[n]
            else:
                assert ptag == 'staffGrp'
                child_ns = [
                    sd.get('n') for sd in parent.iter(f'{{{NS}}}staffDef')
                ]
                assert child_ns
                assert all(staff_roles[n] in REALIZATION for n in child_ns)
                part = staff_to_part[child_ns[0]]
            assert instr.get('midi.channel') == str(part['channel'])
            assert instr.get('midi.instrnum') == str(part['program'])
            assert int(instr.get('midi.instrnum')) == part['program']


def test_corpus_verovio_midi_programs_and_channels():
    """Each staff track uses the role's program; realization share a channel."""
    manifest = load_manifest()
    tk = verovio.toolkit()
    started = time.perf_counter()
    for entry in manifest['works']:
        path = ROOT / entry['file']
        staff_roles = {str(k): v for k, v in entry['staff_roles'].items()}
        ordered_ns = sorted(staff_roles, key=int)
        parts, staff_to_part = expected_parts_from_roles(staff_roles)

        assert tk.loadFile(str(path))
        raw = base64.b64decode(tk.renderToMIDI())
        mid = mido.MidiFile(file=io.BytesIO(raw))
        assert len(mid.tracks) == 1 + len(ordered_ns), entry['key']

        set_tempos = [
            msg for tr in mid.tracks for msg in tr if msg.type == 'set_tempo'
        ]
        assert len(set_tempos) == 1, entry['key']

        staff_channels = {}
        for staff_n, track in zip(ordered_ns, mid.tracks[1:]):
            programs = [m for m in track if m.type == 'program_change']
            note_channels = {
                m.channel for m in track
                if m.type in ('note_on', 'note_off', 'program_change')
            }
            assert len(programs) >= 1, (entry['key'], staff_n)
            channels = {m.channel for m in programs} | note_channels
            assert len(channels) == 1, (entry['key'], staff_n, channels)
            channel = next(iter(channels))
            program = programs[0].program
            assert all(m.program == program for m in programs)
            role = staff_roles[staff_n]
            assert program == EXPECTED_PROGRAM[role], (entry['key'], staff_n, role)
            assert channel == staff_to_part[staff_n]['channel']
            assert channel != 9
            staff_channels[staff_n] = channel

        realization_ns = [n for n in ordered_ns if staff_roles[n] in REALIZATION]
        other_ns = [n for n in ordered_ns if staff_roles[n] not in REALIZATION]
        assert len(realization_ns) == 2
        assert staff_channels[realization_ns[0]] == staff_channels[realization_ns[1]]
        shared = staff_channels[realization_ns[0]]
        assert shared not in {staff_channels[n] for n in other_ns}
        part_channels = {staff_to_part[n]['channel'] for n in other_ns}
        part_channels.add(shared)
        assert len(part_channels) == len(parts)
    elapsed = time.perf_counter() - started
    # 17 Verovio MIDI renders; keep the suite responsive.
    assert elapsed < 120, f'verovio MIDI corpus check took {elapsed:.1f}s'
    print(f'verovio MIDI corpus check: {elapsed:.1f}s')


def test_write_idempotent_and_check_clean(norm, tmp_path):
    mei = prepare(tmp_path, five_staff_score(
        tempo_attrs=' midi.bpm="120" mm="120"',
    ))
    argv = ['--write', '--manifest', 'editorial-works.json']
    code, out, err = run_main(norm, tmp_path, argv)
    assert code == 0, out + err
    after_first = mei.read_bytes()
    assert b'midi.instrnum="40"' in after_first
    assert b'midi.instrname' not in after_first
    assert b'midi.bpm' not in after_first
    assert b' mm=' not in after_first
    code, out, err = run_main(norm, tmp_path, argv)
    assert code == 0, out + err
    assert mei.read_bytes() == after_first
    assert 'changed 0/' in out
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err


def test_check_reports_difference(norm, tmp_path):
    prepare(tmp_path, five_staff_score())
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 1
    assert 'instrDef i1:' in out
    assert 'target=channel 0 program 40 (Violin)' in out


def test_crlf_byte_preservation(norm, tmp_path):
    body = five_staff_score(tempo_attrs=' midi.bpm="90"')
    original = wrap_mei(body).replace('\n', '\r\n')
    mei = tmp_path / 'fixture_corr.mei'
    mei.write_bytes(original.encode('utf-8'))
    (tmp_path / 'editorial-works.json').write_text(json.dumps({
        'works': [{'key': 'fixture', 'file': 'fixture_corr.mei', 'staff_roles': FIVE_ROLES}],
    }))
    assert b'\r\n' in mei.read_bytes()
    crlf_before = mei.read_bytes().count(b'\r\n')
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err
    after = mei.read_bytes()
    assert after.count(b'\r\n') == crlf_before
    assert b'\r\n' in after
    assert b'midi.instrnum="40"' in after
    assert b'midi.instrname' not in after
    assert b'midi.bpm' not in after


def test_mid_piece_instrdef_rewritten(norm, tmp_path):
    mid = '''<scoreDef xml:id="sd2">
<staffGrp xml:id="outer2">
<staffDef xml:id="P1b" n="1" lines="5">
<instrDef xml:id="i1b" midi.channel="15" midi.instrnum="0" midi.volume="77%" />
</staffDef>
<staffDef xml:id="P2b" n="2" lines="5">
<instrDef xml:id="i2b" midi.channel="15" midi.instrnum="0" midi.volume="77%" />
</staffDef>
<staffDef xml:id="P3b" n="3" lines="5">
<instrDef xml:id="i3b" midi.channel="15" midi.instrnum="0" midi.volume="77%" />
</staffDef>
<staffGrp xml:id="brace2">
<instrDef xml:id="i4b" midi.channel="15" midi.instrnum="0" midi.volume="77%" />
<staffDef xml:id="P4b" n="4" lines="5"/>
<staffDef xml:id="P5b" n="5" lines="5"/>
</staffGrp>
</staffGrp>
</scoreDef>'''
    mei = prepare(tmp_path, five_staff_score(mid_score_def=mid))
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err
    text = mei.read_text()
    assert 'xml:id="i1b" midi.channel="0" midi.instrnum="40" midi.volume="77%"' in text
    assert 'xml:id="i4b" midi.channel="3" midi.instrnum="6" midi.volume="77%"' in text
    assert 'midi.instrname' not in text
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err


def test_instrname_removed_and_flagged(norm, tmp_path):
    """A stray midi.instrname is reported by --check and removed by --write."""
    body = five_staff_score(instr_attrs={
        1: 'midi.channel="0" midi.instrnum="40" midi.instrname="Violin" midi.volume="77%"',
        2: 'midi.channel="1" midi.instrnum="42" midi.volume="77%"',
        3: 'midi.channel="2" midi.instrnum="6" midi.volume="77%"',
        4: 'midi.channel="3" midi.instrnum="6" midi.volume="77%"',
    })
    mei = prepare(tmp_path, body)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 1
    assert 'instrDef i1:' in out
    assert 'instrname=Violin' in out
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err
    text = mei.read_text()
    assert 'midi.instrname' not in text
    assert 'midi.instrnum="40"' in text
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err


def test_fail_staff_without_role(norm, tmp_path):
    roles = dict(FIVE_ROLES)
    del roles['2']
    prepare(tmp_path, five_staff_score(), staff_roles=roles)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code != 0
    assert 'staffDef n=\'2\' has no role' in err or 'staffDef n="2" has no role' in err


def test_fail_unknown_role(norm, tmp_path):
    roles = dict(FIVE_ROLES)
    roles['1'] = 'trumpet'
    prepare(tmp_path, five_staff_score(), staff_roles=roles)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code != 0
    assert "unknown role 'trumpet'" in err


def test_fail_part_missing_opening_instrdef(norm, tmp_path):
    body = '''<scoreDef xml:id="sd1">
<staffGrp xml:id="outer">
<staffDef xml:id="P1" n="1" lines="5">
<instrDef xml:id="i1" midi.channel="0" midi.instrnum="0" midi.volume="77%" />
</staffDef>
<staffDef xml:id="P2" n="2" lines="5"/>
<staffDef xml:id="P3" n="3" lines="5">
<instrDef xml:id="i3" midi.channel="2" midi.instrnum="0" midi.volume="77%" />
</staffDef>
<staffGrp xml:id="brace">
<instrDef xml:id="i4" midi.channel="0" midi.instrnum="0" midi.volume="77%" />
<staffDef xml:id="P4" n="4" lines="5"/>
<staffDef xml:id="P5" n="5" lines="5"/>
</staffGrp>
</staffGrp>
</scoreDef>
<section><measure n="1"><staff n="1"><layer n="1">
<note xml:id="n1" dur="4" oct="4" pname="c"/>
</layer></staff></measure></section>'''
    prepare(tmp_path, body)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code != 0
    assert 'has no instrDef in the opening scoreDef' in err


def test_fail_instrdef_on_realization_staffdef(norm, tmp_path):
    body = '''<scoreDef xml:id="sd1">
<staffGrp xml:id="outer">
<staffDef xml:id="P1" n="1" lines="5">
<instrDef xml:id="i1" midi.channel="0" midi.instrnum="0" midi.volume="77%" />
</staffDef>
<staffDef xml:id="P2" n="2" lines="5">
<instrDef xml:id="i2" midi.channel="1" midi.instrnum="0" midi.volume="77%" />
</staffDef>
<staffDef xml:id="P3" n="3" lines="5">
<instrDef xml:id="i3" midi.channel="2" midi.instrnum="0" midi.volume="77%" />
</staffDef>
<staffGrp xml:id="brace">
<staffDef xml:id="P4" n="4" lines="5">
<instrDef xml:id="i4bad" midi.channel="3" midi.instrnum="0" midi.volume="77%" />
</staffDef>
<staffDef xml:id="P5" n="5" lines="5"/>
</staffGrp>
</staffGrp>
</scoreDef>
<section><measure n="1"><staff n="1"><layer n="1">
<note xml:id="n1" dur="4" oct="4" pname="c"/>
</layer></staff></measure></section>'''
    prepare(tmp_path, body)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code != 0
    assert 'sits in realization staffDef' in err


def test_fail_instrdef_on_non_realization_staffgrp(norm, tmp_path):
    body = '''<scoreDef xml:id="sd1">
<staffGrp xml:id="outer">
<staffGrp xml:id="upper">
<instrDef xml:id="ibad" midi.channel="0" midi.instrnum="0" midi.volume="77%" />
<staffDef xml:id="P1" n="1" lines="5"/>
<staffDef xml:id="P2" n="2" lines="5"/>
<staffDef xml:id="P3" n="3" lines="5"/>
</staffGrp>
<staffGrp xml:id="brace">
<instrDef xml:id="i4" midi.channel="3" midi.instrnum="0" midi.volume="77%" />
<staffDef xml:id="P4" n="4" lines="5"/>
<staffDef xml:id="P5" n="5" lines="5"/>
</staffGrp>
</staffGrp>
</scoreDef>
<section><measure n="1"><staff n="1"><layer n="1">
<note xml:id="n1" dur="4" oct="4" pname="c"/>
</layer></staff></measure></section>'''
    prepare(tmp_path, body)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code != 0
    assert "instrDef 'ibad'" in err
    assert 'staffDef n=1' in err or "staffDef n='1'" in err or 'staffDef n="1"' in err


def test_fail_instrdef_on_staffgrp_with_nested_non_realization(norm, tmp_path):
    """Realization brace that also nests a non-realization staff must fail."""
    body = '''<scoreDef xml:id="sd1">
<staffGrp xml:id="outer">
<staffDef xml:id="P1" n="1" lines="5">
<instrDef xml:id="i1" midi.channel="0" midi.instrnum="40" midi.volume="77%" />
</staffDef>
<staffDef xml:id="P2" n="2" lines="5">
<instrDef xml:id="i2" midi.channel="1" midi.instrnum="42" midi.volume="77%" />
</staffDef>
<staffDef xml:id="P3" n="3" lines="5">
<instrDef xml:id="i3" midi.channel="2" midi.instrnum="6" midi.volume="77%" />
</staffDef>
<staffGrp xml:id="brace">
<instrDef xml:id="imixed" midi.channel="3" midi.instrnum="6" midi.volume="77%" />
<staffDef xml:id="P4" n="4" lines="5"/>
<staffDef xml:id="P5" n="5" lines="5"/>
<staffGrp xml:id="nested">
<staffDef xml:id="P1nest" n="1" lines="5"/>
</staffGrp>
</staffGrp>
</staffGrp>
</scoreDef>
<section><measure n="1"><staff n="1"><layer n="1">
<note xml:id="n1" dur="4" oct="4" pname="c"/>
</layer></staff></measure></section>'''
    prepare(tmp_path, body)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code != 0
    assert "instrDef 'imixed'" in err
    assert "descendant staffDef n=1" in err or "staffDef n=1" in err


def test_scoredef_midi_bpm_removed(norm, tmp_path):
    body = five_staff_score(instr_attrs={
        1: 'midi.channel="0" midi.instrnum="40" midi.volume="77%"',
        2: 'midi.channel="1" midi.instrnum="42" midi.volume="77%"',
        3: 'midi.channel="2" midi.instrnum="6" midi.volume="77%"',
        4: 'midi.channel="3" midi.instrnum="6" midi.volume="77%"',
    }).replace(
        '<scoreDef xml:id="sd1">',
        '<scoreDef xml:id="sd1" midi.bpm="90">',
    )
    mei = prepare(tmp_path, body)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 1
    assert '<scoreDef>' in out and 'midi.bpm' in out
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err
    after = mei.read_text()
    assert 'midi.bpm' not in after
    assert 'xml:id="sd1"' in after
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0
    assert mei.read_text() == after


def test_staffdef_midi_mspb_removed(norm, tmp_path):
    body = five_staff_score(instr_attrs={
        1: 'midi.channel="0" midi.instrnum="40" midi.volume="77%"',
        2: 'midi.channel="1" midi.instrnum="42" midi.volume="77%"',
        3: 'midi.channel="2" midi.instrnum="6" midi.volume="77%"',
        4: 'midi.channel="3" midi.instrnum="6" midi.volume="77%"',
    }).replace(
        '<staffDef xml:id="P1" n="1" lines="5">',
        '<staffDef xml:id="P1" n="1" lines="5" midi.mspb="500000">',
    )
    mei = prepare(tmp_path, body)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 1
    assert '<staffDef>' in out and 'midi.mspb' in out
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err
    after = mei.read_text()
    assert 'midi.mspb' not in after
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0
    assert mei.read_text() == after


def test_multiline_tempo_midi_bpm_removed(norm, tmp_path):
    body = five_staff_score(instr_attrs={
        1: 'midi.channel="0" midi.instrnum="40" midi.volume="77%"',
        2: 'midi.channel="1" midi.instrnum="42" midi.volume="77%"',
        3: 'midi.channel="2" midi.instrnum="6" midi.volume="77%"',
        4: 'midi.channel="3" midi.instrnum="6" midi.volume="77%"',
    }).replace(
        '<tempo xml:id="t1" staff="1" tstamp="1">Adagio.</tempo>',
        '<tempo xml:id="t1" staff="1" tstamp="1"\n'
        ' midi.bpm="72">Adagio.</tempo>',
    )
    mei = prepare(tmp_path, body)
    assert 'midi.bpm="72"' in mei.read_text()
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 1
    assert '<tempo>' in out and 'midi.bpm' in out
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err
    after = mei.read_text()
    assert 'midi.bpm' not in after
    assert 'Adagio.' in after
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0
    assert mei.read_text() == after


def test_instrdef_combined_program_and_rate_rewrite(norm, tmp_path):
    """One start-tag rewrite covers channel/program, drops bpm and instrname."""
    body = five_staff_score(instr_attrs={
        1: (
            'midi.channel="0" midi.instrnum="0" midi.instrname="Acoustic_Grand_Piano" '
            'midi.bpm="90" midi.volume="77%"'
        ),
        2: 'midi.channel="1" midi.instrnum="42" midi.volume="77%"',
        3: 'midi.channel="2" midi.instrnum="6" midi.volume="77%"',
        4: 'midi.channel="3" midi.instrnum="6" midi.volume="77%"',
    })
    # Sentinel element after the first instrDef must survive the rewrite.
    body = body.replace(
        '<instrDef xml:id="i1" midi.channel="0" midi.instrnum="0" '
        'midi.instrname="Acoustic_Grand_Piano" midi.bpm="90" midi.volume="77%" />\n'
        '</staffDef>',
        '<instrDef xml:id="i1" midi.channel="0" midi.instrnum="0" '
        'midi.instrname="Acoustic_Grand_Piano" midi.bpm="90" midi.volume="77%" />\n'
        '<clef xml:id="clef_keep" shape="G" line="2" />\n'
        '</staffDef>',
        1,
    )
    mei = prepare(tmp_path, body)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 1, out + err
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err
    text = mei.read_text()
    assert 'xml:id="i1" midi.channel="0" midi.instrnum="40" midi.volume="77%"' in text
    assert 'midi.instrname' not in text
    assert 'midi.bpm' not in text
    assert 'xml:id="clef_keep"' in text
    assert 'xml:id="i2"' in text and 'xml:id="n1"' in text
    after = mei.read_bytes()
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err
    assert mei.read_bytes() == after


def test_tempo_label_keeps_embedded_midi_bpm_text(norm, tmp_path):
    body = five_staff_score(instr_attrs={
        1: 'midi.channel="0" midi.instrnum="40" midi.volume="77%"',
        2: 'midi.channel="1" midi.instrnum="42" midi.volume="77%"',
        3: 'midi.channel="2" midi.instrnum="6" midi.volume="77%"',
        4: 'midi.channel="3" midi.instrnum="6" midi.volume="77%"',
    }).replace(
        '<tempo xml:id="t1" staff="1" tstamp="1">Adagio.</tempo>',
        '<tempo xml:id="t1" label="Keep midi.bpm=\'90\' here" midi.bpm="90" '
        'staff="1" tstamp="1">Adagio.</tempo>',
    )
    mei = prepare(tmp_path, body)
    label = 'label="Keep midi.bpm=\'90\' here"'
    assert label in mei.read_text()
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 1
    assert 'midi.bpm' in out
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err
    text = mei.read_text()
    assert label in text
    tempo = etree.fromstring(text.encode()).find(f'.//{{{NS}}}tempo')
    assert tempo.get('label') == "Keep midi.bpm='90' here"
    assert tempo.get('midi.bpm') is None


def test_commented_tempo_midi_bpm_untouched(norm, tmp_path):
    body = five_staff_score(instr_attrs={
        1: 'midi.channel="0" midi.instrnum="40" midi.volume="77%"',
        2: 'midi.channel="1" midi.instrnum="42" midi.volume="77%"',
        3: 'midi.channel="2" midi.instrnum="6" midi.volume="77%"',
        4: 'midi.channel="3" midi.instrnum="6" midi.volume="77%"',
    }).replace(
        '<tempo xml:id="t1" staff="1" tstamp="1">Adagio.</tempo>',
        '<!-- <tempo xml:id="t_comment" midi.bpm="90">Adagio.</tempo> -->\n'
        '<tempo xml:id="t1" staff="1" tstamp="1">Adagio.</tempo>',
    )
    mei = prepare(tmp_path, body)
    before = mei.read_text()
    assert '<!-- <tempo xml:id="t_comment" midi.bpm="90">Adagio.</tempo> -->' in before
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err
    code, out, err = run_main(norm, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err
    assert mei.read_text() == before


def test_apply_span_edits_rejects_overlap(norm):
    with pytest.raises(ValueError, match='overlapping edits'):
        norm.apply_span_edits('abcdefgh', [(0, 4, 'XX'), (2, 6, 'YY')])


def test_doctype_internal_subset_raises(norm, tmp_path):
    body = five_staff_score(instr_attrs={
        1: 'midi.channel="0" midi.instrnum="40" midi.volume="77%"',
        2: 'midi.channel="1" midi.instrnum="42" midi.volume="77%"',
        3: 'midi.channel="2" midi.instrnum="6" midi.volume="77%"',
        4: 'midi.channel="3" midi.instrnum="6" midi.volume="77%"',
    })
    mei = prepare(tmp_path, body)
    text = mei.read_text()
    text = text.replace(
        f'<mei xmlns="{NS}">',
        f'<!DOCTYPE mei [\n<!ELEMENT mei ANY>\n]>\n<mei xmlns="{NS}">',
        1,
    )
    mei.write_text(text)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code != 0
    assert 'internal DTD subsets are not supported' in err
    assert 'fixture_corr.mei' in err


def test_doctype_plain_system_skipped(norm, tmp_path):
    body = five_staff_score(instr_attrs={
        1: 'midi.channel="0" midi.instrnum="40" midi.volume="77%"',
        2: 'midi.channel="1" midi.instrnum="42" midi.volume="77%"',
        3: 'midi.channel="2" midi.instrnum="6" midi.volume="77%"',
        4: 'midi.channel="3" midi.instrnum="6" midi.volume="77%"',
    })
    mei = prepare(tmp_path, body)
    text = mei.read_text()
    text = text.replace(
        f'<mei xmlns="{NS}">',
        f'<!DOCTYPE mei SYSTEM "http://example.org/mei.dtd">\n'
        f'<mei xmlns="{NS}">',
        1,
    )
    mei.write_text(text)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 0, out + err


def test_fail_staff_without_role_in_music(norm, tmp_path):
    body = five_staff_score(instr_attrs={
        1: 'midi.channel="0" midi.instrnum="40" midi.volume="77%"',
        2: 'midi.channel="1" midi.instrnum="42" midi.volume="77%"',
        3: 'midi.channel="2" midi.instrnum="6" midi.volume="77%"',
        4: 'midi.channel="3" midi.instrnum="6" midi.volume="77%"',
    }).replace(
        '</measure>',
        '<staff n="99"><layer n="1">'
        '<note xml:id="orphan" dur="4" oct="4" pname="c"/>'
        '</layer></staff>\n</measure>',
        1,
    )
    prepare(tmp_path, body)
    code, out, err = run_main(norm, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code != 0
    assert "staff n='99' has no role" in err or 'staff n="99" has no role' in err


def test_corpus_guard_skips_comments():
    """Comments must not crash the independent corpus attribute guard."""
    xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<mei xmlns="{NS}">\n'
        f'<!-- <tempo midi.bpm="90"/> -->\n'
        f'<meiHead><fileDesc><titleStmt><title>x</title></titleStmt>'
        f'<pubStmt/></fileDesc></meiHead>\n'
        f'<music><body><mdiv><score>\n'
        f'<scoreDef><staffGrp>\n'
        f'<staffDef n="1" lines="5">'
        f'<instrDef xml:id="i1" midi.channel="0" midi.instrnum="40" />'
        f'</staffDef>\n'
        f'</staffGrp></scoreDef>\n'
        f'<section><measure n="1"><staff n="1"><layer n="1">'
        f'<note xml:id="n1" dur="4" oct="4" pname="c"/>'
        f'</layer></staff>'
        f'<tempo xml:id="t1" staff="1" tstamp="1">Adagio.</tempo>'
        f'</measure></section>\n'
        f'</score></mdiv></body></music></mei>\n'
    )
    root = etree.fromstring(xml.encode())
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        for name in FORBIDDEN_ANY:
            assert name not in el.attrib
        if etree.QName(el).localname == 'tempo':
            for name in FORBIDDEN_TEMPO:
                assert name not in el.attrib
            assert ''.join(el.itertext()).strip()


def test_midi_channels_skip_percussion(norm):
    assert norm.midi_channels(4) == [0, 1, 2, 3]
    assert norm.midi_channels(10) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 10]
    assert 9 not in norm.midi_channels(15)
