"""musical_lint: accid_ges_mismatch shares the regeneration rule; --out outside ROOT."""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://www.music-encoding.org/ns/mei'

C_MAJOR = (
    '<scoreDef><staffGrp>'
    '<staffDef n="1" lines="5"><keySig sig="0"/></staffDef>'
    '</staffGrp></scoreDef>'
)
F_MAJOR = (
    '<scoreDef><staffGrp>'
    '<staffDef n="1" lines="5"><keySig sig="1f"/></staffDef>'
    '</staffGrp></scoreDef>'
)


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
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
def lint():
    return load('ddt_musical_lint', 'scripts/musical_lint.py')


@pytest.fixture
def regen():
    return load('ddt_regenerate_accid_ges_for_lint', 'scripts/regenerate_accid_ges.py')


def prepare(tmp_path, score_def, body):
    """One-work checkout under tmp_path with the profile main() reads."""
    mei = tmp_path / 'fixture_corr.mei'
    mei.write_text(wrap(score_def, body))
    (tmp_path / 'validation').mkdir()
    (tmp_path / 'validation' / 'editorial-works.json').write_text(json.dumps({
        'works': [{'key': 'fixture', 'file': 'fixture_corr.mei'}],
    }))
    (tmp_path / 'validation' / 'profile.json').write_text(json.dumps({
        'event_elements': ['note', 'chord', 'rest', 'tie'],
    }))
    return mei


def run_lint(lint, tmp_path, argv):
    original = lint.ROOT
    lint.ROOT = tmp_path
    buf = io.StringIO()
    old_argv = sys.argv
    try:
        sys.argv = ['musical_lint.py', *argv]
        with redirect_stdout(buf):
            code = lint.main()
    finally:
        sys.argv = old_argv
        lint.ROOT = original
    # main() returns None; sys.exit(None) is 0. Confirm git show fails outside a repo.
    return (0 if code is None else code), buf.getvalue()


def mismatch_rows(path):
    with path.open(newline='') as handle:
        return [r for r in csv.DictReader(handle) if r['check'] == 'accid_ges_mismatch']


def test_git_show_fails_outside_repo(tmp_path):
    """id_churn's git show fails harmlessly when ROOT is not a checkout."""
    result = subprocess.run(
        ['git', '-C', str(tmp_path), 'show', 'v0.9.0:fixture_corr.mei'],
        capture_output=True,
    )
    assert result.returncode != 0


def test_tie_chain_reports_every_stale_note(lint, tmp_path):
    # Old lint licensed successors from Work.alters (file with accid.ges), so only
    # the first note of a stale tie chain was reported. Regeneration strips ges
    # first; every note of the chain must appear.
    body = '''<section>
<measure n="1" xml:id="m1">
<staff n="1"><layer n="1">
<note xml:id="t1" dur="4" oct="4" pname="c" accid.ges="s" tie="i" />
</layer></staff>
<tie startid="#t1" endid="#t2" />
</measure>
<measure n="2" xml:id="m2">
<staff n="1"><layer n="1">
<note xml:id="t2" dur="4" oct="4" pname="c" accid.ges="s" tie="m" />
<note xml:id="t3" dur="4" oct="4" pname="c" accid.ges="s" tie="t" />
</layer></staff>
<tie startid="#t2" endid="#t3" />
</measure>
</section>'''
    prepare(tmp_path, C_MAJOR, body)
    out = tmp_path / 'out.csv'
    code, printed = run_lint(lint, tmp_path, [
        '--manifest', 'validation/editorial-works.json', '--out', str(out),
    ])
    assert code == 0, printed
    rows = mismatch_rows(out)
    assert {r['xml_ids'] for r in rows} == {'t1', 't2', 't3'}
    assert all(r['check'] == 'accid_ges_mismatch' for r in rows)


def test_regenerated_fixture_is_clean(lint, regen, tmp_path):
    body = '''<section>
<measure n="1" xml:id="m1">
<staff n="1"><layer n="1">
<note xml:id="b1" dur="4" oct="4" pname="b" />
<note xml:id="f1" dur="4" oct="4" pname="f" accid="s" tie="i" />
<note xml:id="f2" dur="4" oct="4" pname="f" />
</layer></staff>
<tie startid="#f1" endid="#f3" />
</measure>
<measure n="2" xml:id="m2">
<staff n="1"><layer n="1">
<note xml:id="f3" dur="4" oct="4" pname="f" tie="t" />
</layer></staff>
</measure>
</section>'''
    prepare(tmp_path, F_MAJOR, body)
    original_regen = regen.ROOT
    regen.ROOT = tmp_path
    try:
        code = regen.main(['--write', '--manifest', 'validation/editorial-works.json'])
    finally:
        regen.ROOT = original_regen
    assert code == 0
    out = tmp_path / 'out.csv'
    code, printed = run_lint(lint, tmp_path, [
        '--manifest', 'validation/editorial-works.json', '--out', str(out),
    ])
    assert code == 0, printed
    assert mismatch_rows(out) == []


def test_location_only_difference(lint, tmp_path):
    body = '''<section><measure n="1" xml:id="m1">
<staff n="1"><layer n="1">
<note xml:id="beside" dur="4" oct="4" pname="b" accid.ges="f">
<accid xml:id="beside_acc" />
</note>
<note xml:id="written" dur="4" oct="4" pname="f" accid="s" accid.ges="s" />
</layer></staff></measure></section>'''
    prepare(tmp_path, F_MAJOR, body)
    out = tmp_path / 'out.csv'
    code, printed = run_lint(lint, tmp_path, [
        '--manifest', 'validation/editorial-works.json', '--out', str(out),
    ])
    assert code == 0, printed
    rows = mismatch_rows(out)
    by_id = {r['xml_ids']: r for r in rows}
    assert set(by_id) == {'beside', 'written'}
    assert 'on note' in by_id['beside']['detail'] and 'on child' in by_id['beside']['detail']
    assert 'current=s (on note)' in by_id['written']['detail']
    assert 'target=(absent)' in by_id['written']['detail']


def test_cross_staff_chord_reports_its_staff(lint, tmp_path):
    # Regeneration rows give the enclosing <staff>; the lint row must honour the chord's @staff.
    body = '''<section><measure n="1" xml:id="m1">
<staff n="1"><layer n="1">
<chord xml:id="ch1" dur="4" staff="2">
<note xml:id="x1" oct="3" pname="c" accid.ges="s" />
<note xml:id="x2" oct="3" pname="e" />
</chord>
</layer></staff>
<staff n="2"><layer n="1"><rest dur="4" /></layer></staff>
</measure></section>'''
    prepare(tmp_path, C_MAJOR, body)
    out = tmp_path / 'out.csv'
    code, printed = run_lint(lint, tmp_path, [
        '--manifest', 'validation/editorial-works.json', '--out', str(out),
    ])
    assert code == 0, printed
    rows = mismatch_rows(out)
    assert [(r['xml_ids'], r['staff']) for r in rows] == [('x1', '2')]

def test_out_absolute_and_relative(lint, tmp_path):
    body = '''<section><measure n="1" xml:id="m1">
<staff n="1"><layer n="1">
<note xml:id="c1" dur="4" oct="4" pname="c" />
</layer></staff></measure></section>'''
    prepare(tmp_path, C_MAJOR, body)

    outside = tmp_path.parent / f'lint-outside-{tmp_path.name}.csv'
    code, printed = run_lint(lint, tmp_path, [
        '--manifest', 'validation/editorial-works.json', '--out', str(outside),
    ])
    assert code == 0, printed
    assert outside.is_file()
    assert str(outside) in printed
    outside.unlink(missing_ok=True)

    code, printed = run_lint(lint, tmp_path, [
        '--manifest', 'validation/editorial-works.json', '--out', 'relative-out.csv',
    ])
    assert code == 0, printed
    assert (tmp_path / 'relative-out.csv').is_file()
    assert printed.rstrip().endswith('relative-out.csv')


def barline_rows(path):
    with path.open(newline='') as handle:
        return {(r['check'], r['measure']) for r in csv.DictReader(handle)
                if r['check'] in {'final_barline_inside_work', 'work_end_barline'}}


def one_note_measure(n, attributes='', control=''):
    return (f'<measure n="{n}" xml:id="m{n}"{attributes}>'
            f'<staff n="1"><layer n="1"><note xml:id="n{n}" dur="1" oct="4" pname="c" /></layer></staff>'
            f'{control}</measure>')


@pytest.mark.parametrize('measures, expected', [
    # App. II mm. 31/68: a page-end final barline inside the work; Op. II/4: a work ending on a double bar.
    ([one_note_measure(1, ' right="end"'), one_note_measure(2, ' right="dbl"')],
     {('final_barline_inside_work', '1'), ('work_end_barline', '2')}),
    # Op. II/3 m. 217: a section closing on a fermata and a final barline; App. I ends on a repeat.
    ([one_note_measure(1, ' right="end"', '<fermata staff="1" startid="#n1" />'), one_note_measure(2, ' right="rptend"')],
     set()),
    ([one_note_measure(1), one_note_measure(2, ' right="end"')], set()),
])
def test_barline_checks(lint, tmp_path, measures, expected):
    prepare(tmp_path, C_MAJOR, '<section>' + ''.join(measures) + '</section>')
    out = tmp_path / 'out.csv'
    code, printed = run_lint(lint, tmp_path, ['--manifest', 'validation/editorial-works.json', '--out', str(out)])
    assert code == 0, printed
    assert barline_rows(out) == expected
