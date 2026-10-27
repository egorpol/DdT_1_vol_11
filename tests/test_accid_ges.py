"""@accid.ges is derived from CAMAT's written-notation resolution."""
from __future__ import annotations

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path

import pytest
from camat.check_mei_consistency import strip_accid_ges_text

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://www.music-encoding.org/ns/mei'

F_MAJOR = (
    '<scoreDef><staffGrp>'
    '<staffDef n="1" lines="5"><keySig sig="1f"/></staffDef>'
    '<staffDef n="2" lines="5"><keySig sig="1f"/></staffDef>'
    '</staffGrp></scoreDef>'
)
C_MAJOR = (
    '<scoreDef><staffGrp>'
    '<staffDef n="1" lines="5"><keySig sig="0"/></staffDef>'
    '<staffDef n="2" lines="5"><keySig sig="0"/></staffDef>'
    '</staffGrp></scoreDef>'
)


def module():
    spec = importlib.util.spec_from_file_location(
        'ddt_regenerate_accid_ges', ROOT / 'scripts' / 'regenerate_accid_ges.py'
    )
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def wrap(score_def, body):
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<mei xmlns="{NS}">\n<music><body><mdiv><score>\n'
        f'{score_def}\n{body}\n'
        f'</score></mdiv></body></music></mei>\n'
    )


@pytest.fixture
def regen():
    return module()


def prepare(tmp_path, regen, score_def, body):
    """One-work checkout under tmp_path; patch regen.ROOT for the call."""
    mei = tmp_path / 'fixture_corr.mei'
    mei.write_text(wrap(score_def, body))
    (tmp_path / 'editorial-works.json').write_text(json.dumps({
        'works': [{'key': 'fixture', 'file': 'fixture_corr.mei'}],
    }))
    return mei


def run_main(regen, tmp_path, argv):
    original = regen.ROOT
    regen.ROOT = tmp_path
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            code = regen.main(argv)
    finally:
        regen.ROOT = original
    return code, buf.getvalue()


def targets_by_id(regen, text):
    import xml.etree.ElementTree as ET
    from camat.verovio_backend import _extract_mei_note_effective_alters
    bare, _ = strip_accid_ges_text(text)
    root = ET.fromstring(bare.encode())
    alters = _extract_mei_note_effective_alters(root)
    out = {}
    for note in root.iter(regen.MEI + 'note'):
        alter = alters.get(id(note))
        out[note.get(regen.ID)] = None if alter is None else regen.target_ges(note, alter)
    return out


def ges_locations(text):
    import re
    found = {}
    for match in re.finditer(r'<note\b[^<>\r\n]* xml:id="([^"]*)"[^<>\r\n]*>', text):
        nid, tag = match.group(1), match.group(0)
        if 'accid.ges="' in tag:
            found[nid] = (re.search(r'accid\.ges="([^"]*)"', tag).group(1), 'note')
            continue
        if tag.endswith('/>'):
            continue
        body = text[match.end():text.find('</note>', match.end())]
        child = re.search(r'<accid\b[^<>\r\n]*accid\.ges="([^"]*)"[^<>\r\n]*>', body)
        if child:
            found[nid] = (child.group(1), 'child')
    return found


def test_corpus_accid_ges_matches_camat(regen):
    code, out = run_main(regen, ROOT, ['--check'])
    assert code == 0, out


def test_f_major_octave_specific_carry(regen, tmp_path):
    body = '''<section><measure n="1">
<staff n="1"><layer n="1">
<note xml:id="b1" dur="4" oct="4" pname="b" />
<note xml:id="b2" dur="4" oct="4" pname="b" accid="n" />
<note xml:id="b3" dur="4" oct="4" pname="b" />
<note xml:id="b4" dur="4" oct="5" pname="b" />
</layer></staff></measure></section>'''
    mei = prepare(tmp_path, regen, F_MAJOR, body)
    code, _ = run_main(regen, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    text = mei.read_text()
    assert code == 0
    assert targets_by_id(regen, text) == {'b1': 'f', 'b2': None, 'b3': None, 'b4': 'f'}
    assert ges_locations(text) == {'b1': ('f', 'note'), 'b4': ('f', 'note')}


def test_written_sharp_carry_staff_and_bar(regen, tmp_path):
    body = '''<section>
<measure n="1">
<staff n="1"><layer n="1">
<note xml:id="f1" dur="4" oct="4" pname="f" accid="s" />
<note xml:id="f2" dur="4" oct="4" pname="f" />
</layer></staff>
<staff n="2"><layer n="1">
<note xml:id="f3" dur="4" oct="4" pname="f" />
</layer></staff>
</measure>
<measure n="2">
<staff n="1"><layer n="1">
<note xml:id="f4" dur="4" oct="4" pname="f" />
</layer></staff>
</measure>
</section>'''
    mei = prepare(tmp_path, regen, C_MAJOR, body)
    code, _ = run_main(regen, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    text = mei.read_text()
    assert code == 0
    assert targets_by_id(regen, text) == {'f1': None, 'f2': 's', 'f3': None, 'f4': None}
    assert ges_locations(text) == {'f2': ('s', 'note')}


def test_tie_over_barline(regen, tmp_path):
    body = '''<section>
<measure n="1">
<staff n="1"><layer n="1">
<note xml:id="t1" dur="4" oct="4" pname="f" accid="s" tie="i" />
</layer></staff>
<tie startid="#t1" endid="#t2" />
</measure>
<measure n="2">
<staff n="1"><layer n="1">
<note xml:id="t2" dur="4" oct="4" pname="f" tie="t" />
<note xml:id="t3" dur="4" oct="4" pname="f" />
</layer></staff>
</measure>
</section>'''
    mei = prepare(tmp_path, regen, C_MAJOR, body)
    code, _ = run_main(regen, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    text = mei.read_text()
    assert code == 0
    assert targets_by_id(regen, text) == {'t1': None, 't2': 's', 't3': None}
    assert ges_locations(text) == {'t2': ('s', 'note')}


def test_stale_and_duplicate_removed_child_kept(regen, tmp_path):
    body = '''<section><measure n="1">
<staff n="1"><layer n="1">
<note xml:id="stale" dur="4" oct="4" pname="c" accid.ges="s" />
<note xml:id="dup" dur="4" oct="4" pname="f" accid="s" accid.ges="s" />
<note xml:id="child" dur="4" oct="4" pname="b">
<accid xml:id="childacc" accid.ges="f" />
</note>
</layer></staff></measure></section>'''
    original = wrap(F_MAJOR, body)
    mei = prepare(tmp_path, regen, F_MAJOR, body)
    code, out = run_main(regen, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    text = mei.read_text()
    assert code == 0
    locs = ges_locations(text)
    assert 'stale' not in locs
    assert 'dup' not in locs
    assert locs['child'] == ('f', 'child')
    assert 'removed stale:' in out
    assert 'removed dup:' in out
    assert strip_accid_ges_text(text)[0] == strip_accid_ges_text(original)[0]


def test_write_idempotent_and_check_clean(regen, tmp_path):
    body = '''<section><measure n="1">
<staff n="1"><layer n="1">
<note xml:id="b1" dur="4" oct="4" pname="b" />
<note xml:id="b2" dur="4" oct="4" pname="b" accid="n" />
</layer></staff></measure></section>'''
    mei = prepare(tmp_path, regen, F_MAJOR, body)
    argv = ['--write', '--manifest', 'editorial-works.json']
    assert run_main(regen, tmp_path, argv)[0] == 0
    after_first = mei.read_text()
    code, out = run_main(regen, tmp_path, argv)
    assert code == 0
    assert mei.read_text() == after_first
    assert 'added 0' in out and 'removed 0' in out
    code, out = run_main(regen, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 0, out


def test_check_reports_difference(regen, tmp_path):
    body = '''<section><measure n="1">
<staff n="1"><layer n="1">
<note xml:id="b1" dur="4" oct="4" pname="b" />
</layer></staff></measure></section>'''
    prepare(tmp_path, regen, F_MAJOR, body)
    code, out = run_main(regen, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 1
    assert 'note b1: current=(absent) (absent) target=f (on note)' in out


def test_all_accid_ges_locations_considered(regen, tmp_path):
    """A correct value must not hide a stale second location."""
    body = '''<section><measure n="1">
<staff n="1"><layer n="1">
<note xml:id="note_keeps" dur="4" oct="4" pname="b" accid.ges="f">
<accid xml:id="stale_child" accid.ges="n" />
</note>
<note xml:id="child_keeps" dur="4" oct="4" pname="b" accid.ges="n">
<accid xml:id="good_child" accid.ges="f" />
</note>
</layer></staff></measure></section>'''
    original = wrap(F_MAJOR, body)
    mei = prepare(tmp_path, regen, F_MAJOR, body)
    code, out = run_main(regen, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 1
    assert 'note_keeps' in out and 'child_keeps' in out
    code, out = run_main(regen, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0
    text = mei.read_text()
    assert ges_locations(text) == {
        'note_keeps': ('f', 'child'),
        'child_keeps': ('f', 'child'),
    }
    assert 'accid.ges="n"' not in text
    assert 'removed note_keeps:' in out
    assert 'removed child_keeps:' in out
    assert strip_accid_ges_text(text)[0] == strip_accid_ges_text(original)[0]
    code, out = run_main(regen, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 0, out


def test_value_goes_on_accid_child(regen, tmp_path):
    """Verovio warns when a note and its <accid> child both carry an accidental."""
    body = '''<section><measure n="1">
<staff n="1"><layer n="1">
<note xml:id="empty" dur="4" oct="4" pname="b">
<accid xml:id="empty_acc" glyph.auth="smufl" />
</note>
<note xml:id="beside" dur="4" oct="5" pname="b" accid.ges="f">
<accid xml:id="beside_acc" />
</note>
</layer></staff></measure></section>'''
    original = wrap(F_MAJOR, body)
    mei = prepare(tmp_path, regen, F_MAJOR, body)
    code, out = run_main(regen, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 1
    assert 'note beside: current=f (on note) target=f (on child <accid xml:id="beside_acc">)' in out
    code, out = run_main(regen, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0
    text = mei.read_text()
    assert ges_locations(text) == {'empty': ('f', 'child'), 'beside': ('f', 'child')}
    assert '<accid xml:id="empty_acc" glyph.auth="smufl" accid.ges="f" />' in text
    assert strip_accid_ges_text(text)[0] == strip_accid_ges_text(original)[0]
    code, out = run_main(regen, tmp_path, ['--check', '--manifest', 'editorial-works.json'])
    assert code == 0, out


def test_crlf_byte_preservation(regen, tmp_path):
    body = '''<section><measure n="1">
<staff n="1"><layer n="1">
<note xml:id="b1" dur="4" oct="4" pname="b" />
<note xml:id="b2" dur="4" oct="4" pname="b" accid="n" />
</layer></staff></measure></section>'''
    original = wrap(F_MAJOR, body).replace('\n', '\r\n')
    mei = tmp_path / 'fixture_corr.mei'
    mei.write_bytes(original.encode('utf-8'))
    (tmp_path / 'editorial-works.json').write_text(json.dumps({
        'works': [{'key': 'fixture', 'file': 'fixture_corr.mei'}],
    }))
    assert b'\r\n' in mei.read_bytes()
    code, _ = run_main(regen, tmp_path, ['--write', '--manifest', 'editorial-works.json'])
    assert code == 0
    after = mei.read_bytes()
    assert after.count(b'\r\n') == original.encode('utf-8').count(b'\r\n')
    assert b'\r\n' in after
    stripped_after, _ = strip_accid_ges_text(after.decode('utf-8'))
    stripped_before, _ = strip_accid_ges_text(original)
    assert stripped_after.encode('utf-8') == stripped_before.encode('utf-8')
    assert b'accid.ges="f"' in after
