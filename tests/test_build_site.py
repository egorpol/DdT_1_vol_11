from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

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
    assert [(w['id'], w['status']) for w in pending] == [('op2_01', 'pending')]
    listed = json.loads((ROOT / 'validation/editorial-works.json').read_text(encoding='utf-8'))['works']
    assert {w['key'] for w in works if 'mei' in w} == {w['key'] for w in listed}
    for work in works:
        if 'mei' in work:
            assert digest(out / work['mei']) == digest(ROOT / work['source'])
            assert (ROOT / work['report']).is_file()
    for name in ('index.html', 'viewer.css', 'viewer.js'):
        assert (out / name).read_bytes() == (ROOT / 'site' / name).read_bytes()
    manifest = json.loads((out / 'supplemental_material/manifest.json').read_text(encoding='utf-8'))
    assert manifest['items']
    for item in manifest['items']:
        assert digest(out / item['file']) == item['sha256']
        assert item['work_key'] in {w['key'] for w in works}


def test_build_refuses_to_empty_the_repository(monkeypatch):
    m = module()
    monkeypatch.setattr('sys.argv', ['build_site.py', str(ROOT)])
    assert m.main() == 1
