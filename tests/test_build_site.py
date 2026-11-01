from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location('ddt_build_site', ROOT / 'scripts/build_site.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_site_index_lists_every_work_and_copies_the_listed_files(tmp_path):
    out = tmp_path / '_site'
    index = module().build(out)
    works = index['works']
    assert [w['label'] for w in works] == [
        'Op. I/1', 'Op. I/2', 'Op. I/3', 'Op. I/4', 'Op. I/5', 'Op. I/6', 'Op. I/7',
        'Op. II/1', 'Op. II/2', 'Op. II/3', 'Op. II/4', 'Op. II/5', 'Op. II/6', 'Op. II/7',
        'App. I', 'App. II', 'App. III',
    ]
    assert json.loads((out / 'works.json').read_text(encoding='utf-8')) == index
    pending = [w for w in works if 'mei' not in w]
    assert pending == []
    assert next(w for w in works if w['id'] == 'op2_01')['status'] == 'corrected'
    listed = json.loads((ROOT / 'validation/editorial-works.json').read_text(encoding='utf-8'))['works']
    assert {w['key'] for w in works if 'mei' in w} == {w['key'] for w in listed}
    for work in works:
        if 'mei' in work:
            assert digest(out / work['mei']) == digest(ROOT / work['source'])
            assert (ROOT / work['report']).is_file()
    for name in ('index.html', 'viewer.css', 'viewer.js', 'player.js'):
        assert (out / name).read_bytes() == (ROOT / 'site' / name).read_bytes()
    manifest = json.loads((out / 'supplemental_material/manifest.json').read_text(encoding='utf-8'))
    assert manifest['items']
    for item in manifest['items']:
        assert digest(out / item['file']) == item['sha256']
        assert item['work_key'] in {w['key'] for w in works}


def test_build_refuses_to_empty_the_repository_or_its_folders(monkeypatch):
    m = module()
    def refuse(path):
        raise AssertionError(f'would delete {path}')
    monkeypatch.setattr(m.shutil, 'rmtree', refuse)
    for out in (ROOT, ROOT.parent, ROOT / 'site', ROOT / '11_buxtehude_sonatas_final'):
        monkeypatch.setattr('sys.argv', ['build_site.py', str(out)])
        assert m.main() == 1


def test_build_rejects_an_excerpt_that_does_not_match_its_mei_or_image():
    m = module()
    item = json.loads((ROOT / 'supplemental_material/manifest.json').read_text(encoding='utf-8'))['items'][0]
    listed = json.loads((ROOT / 'validation/editorial-works.json').read_text(encoding='utf-8'))['works']
    files = {w['key']: w['file'] for w in listed}
    m.check_excerpt(item, files)
    for change in ({'measure': 99999}, {'event_id': 'no-such-event'}, {'annotation_id': 'no-such-annot'},
                   {'width': item['width'] + 1}, {'sha256': '0' * 64}, {'work_key': 'op2_02_sonata_d_major'}):
        with pytest.raises(SystemExit):
            m.check_excerpt({**item, **change}, files)


def test_a_pending_entry_drops_out_once_its_work_is_listed(tmp_path, monkeypatch):
    m = module()
    monkeypatch.setattr(m, 'PENDING', m.PENDING + [{**m.PENDING[0], 'key': 'op1_01_sonata_f_major'}])
    works = m.build(tmp_path / '_site')['works']
    assert [w['id'] for w in works].count('op1_01') == 1
    assert 'mei' in next(w for w in works if w['id'] == 'op1_01')


def test_parts_match_the_mei_programs_roles_and_labels(tmp_path):
    m = module()
    from normalize_midi_data import ROLE_PROGRAM
    works = [w for w in m.build(tmp_path / '_site')['works'] if 'mei' in w]
    assert sum(len(w['parts']) for w in works) == 69
    for work in works:
        parts = work['parts']
        opening = m.ET.parse(ROOT / work['source']).getroot().find(f'.//{m.MEI}music//{m.MEI}scoreDef')
        encoded = {int(i.get('midi.channel')): int(i.get('midi.instrnum')) for i in opening.iter(f'{m.MEI}instrDef')}
        assert [p['channel'] for p in parts] == sorted(encoded)
        assert len({p['channel'] for p in parts}) == len(parts)
        assert {p['channel']: p['program'] for p in parts} == encoded
        realization = [p for p in parts if p['role'] == 'keyboard_realization']
        assert len(realization) == 1
        assert realization[0]['label'] == 'Realization (Stiehl)'
        for part in parts:
            role = 'keyboard_realization_upper' if part['role'] == 'keyboard_realization' else part['role']
            assert part['program'] == ROLE_PROGRAM[role][0]
            assert part['label'] and not part['label'].endswith('.')
    labels = {w['id']: [p['label'] for p in w['parts']] for w in works}
    assert labels['op1_02'] == ['Violin', 'Viola da gamba', 'Continuo', 'Realization (Stiehl)']
    assert labels['app_01'] == ['Violino', 'Viola da gamba', 'Continuo', 'Realization (Stiehl)']
    assert labels['app_02'] == ['Violino I', 'Violino II', 'Viola di gamba', 'Continuo', 'Realization (Stiehl)']
    assert labels['app_03'] == ['Viola da Gamba', 'Violone', 'Continuo', 'Realization (Stiehl)']
    assert labels['op2_05'] == ['Violino', 'Viola da gamba', 'Cembalo', 'Realization (Stiehl)']
    assert labels['op1_03'][1] == 'Viola da gramba'


def test_build_rejects_a_disagreeing_mei_channel(tmp_path, monkeypatch):
    m = module()
    work = json.loads((ROOT / m.WORK_LIST).read_text(encoding='utf-8'))['works'][0]
    parse = m.ET.parse

    def changed_parse(path):
        tree = parse(path)
        if Path(path) == ROOT / work['file']:
            instr = next(tree.getroot().iter(f'{m.MEI}instrDef'))
            instr.set('midi.channel', '15')
        return tree

    monkeypatch.setattr(m.ET, 'parse', changed_parse)
    with pytest.raises(SystemExit, match=rf"{work['key']}, staff 1: midi.channel"):
        m.build(tmp_path / '_site')
