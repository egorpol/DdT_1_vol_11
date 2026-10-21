from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location('ddt_' + name, ROOT / 'scripts' / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_empty_selection_and_report_input_overlap_are_rejected():
    corpus = module('validate_corpus')
    with pytest.raises(ValueError, match='at least one'):
        corpus.plan_corpus_validation(work_keys=[])
    with pytest.raises(ValueError, match='must not contain'):
        corpus.plan_corpus_validation(output_dir=ROOT)


def test_duplicate_manifest_file_and_escaped_schema_are_rejected(tmp_path):
    corpus = module('validate_corpus')
    manifest = json.loads((ROOT / 'validation/works.json').read_text())
    extra = copy.deepcopy(manifest['works'][0])
    extra['key'] = 'another-identity-for-the-same-file'
    manifest['works'].append(extra)
    path = tmp_path / 'duplicate.json'
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='distinct MEI'):
        corpus.plan_corpus_validation(manifest=path)
    profile = json.loads((ROOT / 'validation/profile.json').read_text())
    profile['schema'] = '../outside.rng'
    path = tmp_path / 'profile.json'
    path.write_text(json.dumps(profile))
    with pytest.raises(ValueError, match='schema must stay'):
        corpus.plan_corpus_validation(profile=path)


def fake_general(monkeypatch, *, warning=False):
    from camat.mei_validation import DEFAULT_REQUIRED, ValidationResult
    import camat.mei_validation as shared
    called = {}
    def run(files, **options):
        called.update(options)
        findings = [{'severity': 'warning', 'category': 'schematron', 'check': 'schema-warning',
                     'message': 'Review this external reference.'}] if warning else []
        record = {
            'conformance': 'passed', 'required_checks_status': 'passed',
            'consumer_diagnostics': 'passed', 'completion_status': 'completed',
            'schema': {'sha256': hashlib.sha256(options['schema'].read_bytes()).hexdigest()},
            'inputs': [{'path': str(path), 'sha256_before': hashlib.sha256(path.read_bytes()).hexdigest()}
                       for path in files],
            'executions': {name: {'status': 'passed'} for name in DEFAULT_REQUIRED},
        }
        result = ValidationResult(findings, record)
        result.write(options['output_dir'])
        return result
    monkeypatch.setattr(shared, 'run_mei_validation', run)
    return called


def test_publication_warning_is_pending_in_review_not_waived(tmp_path, monkeypatch):
    corpus = module('validate_corpus')
    fake_general(monkeypatch, warning=True)
    monkeypatch.setattr(corpus, 'edition_rows', lambda *a, **kw: [])
    result = corpus.run_corpus_validation(output_dir=tmp_path / 'run')
    assert result.record['mei_conformance'] == 'passed'
    assert result.record['ddt']['publication_acceptance'] == 'needs-review'
    assert any(row['check'] == 'ddt.schematron_warnings' for row in result.findings)
    assert corpus.corpus_exit_code(result) == 0
    general = json.loads((tmp_path / 'run/general/findings.json').read_text())
    assert len(general) == 1 and general[0]['category'] == 'schematron'


def test_release_forces_consumers_and_blocks_pending_warnings(tmp_path, monkeypatch):
    corpus = module('validate_corpus')
    called = fake_general(monkeypatch, warning=True)
    monkeypatch.setattr(corpus, 'edition_rows', lambda *a, **kw: [])
    result = corpus.run_corpus_validation(mode='release', output_dir=tmp_path / 'run')
    assert called['check_verovio'] and called['check_camat_parse']
    assert {'verovio', 'camat_parse'} <= set(called['required_checks'])
    assert corpus.corpus_exit_code(result) == 1
    assert any(row['check'] == 'ddt.schematron_warnings' and row['severity'] == 'error' for row in result.findings)


def test_policy_execution_failure_cannot_inherit_previous_pass(tmp_path, monkeypatch):
    corpus = module('validate_corpus')
    fake_general(monkeypatch)
    target = tmp_path / 'run'
    target.mkdir()
    (target / 'run.json').write_text('{"ddt":{"publication_acceptance":"passed"}}')
    def broken(*a, **kw):
        raise RuntimeError('policy did not finish')
    monkeypatch.setattr(corpus, 'edition_rows', broken)
    result = corpus.run_corpus_validation(output_dir=target)
    assert result.record['completion_status'] == 'incomplete'
    assert result.record['ddt']['policy_execution_status'] == 'execution-error'
    assert result.record['ddt']['publication_acceptance'] == 'incomplete'
    assert corpus.corpus_exit_code(result) == 1
    assert json.loads((target / 'run.json').read_text())['ddt']['publication_acceptance'] == 'incomplete'


def test_input_hashes_cover_the_local_policy_pass(tmp_path, monkeypatch):
    import shutil
    corpus = module('validate_corpus')
    test_root = tmp_path / 'corpus'
    manifest = json.loads((ROOT / 'validation/works.json').read_text())
    for name in ['validation/works.json', 'validation/profile.json', 'validation/rules.py',
                 'schemas/mei-CMN-5.1.rng', manifest['works'][0]['file']]:
        destination = test_root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    fake_general(monkeypatch)
    def accidental_write(work, *, root_dir, **kwargs):
        path = root_dir / work['file']
        path.write_bytes(path.read_bytes() + b'\n')
        return []
    monkeypatch.setattr(corpus, 'edition_rows', accidental_write)
    result = corpus.run_corpus_validation(root=test_root, output_dir=tmp_path / 'run')
    assert not result.record['inputs'][0]['unchanged']
    assert result.record['mei_conformance'] == 'failed'
    assert corpus.corpus_exit_code(result) == 1


def test_release_compares_selected_mei_with_the_immutable_commit(tmp_path, monkeypatch):
    import shutil
    import subprocess
    corpus = module('validate_corpus')
    # The corpus sits one level below the repository top to cover root-relative blob paths.
    test_root = tmp_path / 'repo/corpus'
    manifest = json.loads((ROOT / 'validation/works.json').read_text())
    mei = manifest['works'][0]['file']
    for name in ['validation/profile.json', 'validation/rules.py', 'schemas/mei-CMN-5.1.rng', mei]:
        destination = test_root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    def git(*args):
        return subprocess.run(['git', '-C', str(test_root.parent), '-c', 'user.name=Test',
                               '-c', 'user.email=test@example.org', *args], check=True,
                              capture_output=True, text=True).stdout.strip()
    git('init', '-q')
    git('add', '.')
    git('commit', '-qm', 'final MEI')
    fake_general(monkeypatch)
    monkeypatch.setattr(corpus, 'edition_rows', lambda *a, **kw: [])
    manifest['release_version'] = '9.9.9'
    def immutable_rows(reference):
        # The manifest is written after the commit it names, as in a real release.
        manifest['immutable_git_ref'] = reference
        (test_root / 'validation/works.json').write_text(json.dumps(manifest))
        result = corpus.run_corpus_validation(root=test_root, mode='release', output_dir=tmp_path / 'run')
        return [(row['check'], row.get('file')) for row in result.findings
                if row['check'] in {'ddt.immutable_commit', 'ddt.immutable_content', 'ddt.release_tag'}]
    commit, original = git('rev-parse', 'HEAD'), (test_root / mei).read_bytes()
    assert immutable_rows(commit) == [('ddt.release_tag', None)]
    git('add', '.')
    git('commit', '-qm', 'manifest')
    git('tag', '-a', '-m', 'release', 'v9.9.9')
    assert immutable_rows(commit) == []
    (test_root / mei).write_bytes(original + b'\n')
    assert immutable_rows(commit) == [('ddt.immutable_content', mei)]
    git('commit', '-qam', 'later edit')
    git('tag', '-f', '-a', '-m', 'moved', 'v9.9.9')
    (test_root / mei).write_bytes(original)
    assert immutable_rows(commit) == [('ddt.release_tag', mei)]
    assert immutable_rows('0' * 40) == [('ddt.immutable_commit', None)]


def viewer_template():
    def cell(identifier, source):
        return {'id': identifier, 'cell_type': 'code', 'metadata': {},
                'source': source.splitlines(keepends=True), 'outputs': [], 'execution_count': None}
    return {'nbformat': 4, 'nbformat_minor': 5, 'metadata': {}, 'cells': [
        {'id': 'intro', 'cell_type': 'markdown', 'metadata': {}, 'source': ['Shared viewer']},
        cell('viewer-path-setup', 'import setup_camat\n'),
        cell('old-input', 'MEI_SOURCE = "demo.mei"\n'),
        cell('viewer-configuration', 'AUTO_WATCH_MEI = False\nZONE_OPACITY = 0.18\n'),
        cell('launch', 'viewer = launch_interactive_facsimile_viewer(MEI_SOURCE)\n'),
    ]}


def test_viewer_sync_preserves_options_adds_new_defaults_and_backs_up(tmp_path):
    sync = module('sync_camat_viewer')
    checkout = tmp_path / 'camat'
    source = checkout / 'notebooks/mei_facsimile_viewer.ipynb'
    source.parent.mkdir(parents=True)
    template = viewer_template()
    source.write_text(json.dumps(template))
    destination = tmp_path / 'viewer.ipynb'
    sync.sync_viewer(checkout=checkout, corpus_root=ROOT, output=destination)
    edited = json.loads(destination.read_text())
    for cell in edited['cells']:
        if cell['id'] == 'viewer-configuration':
            cell['source'] = ['AUTO_WATCH_MEI = True\nZONE_OPACITY = 0.4\n']
        if cell['id'] == 'ddt-viewer-source':
            cell['source'] = ['MEI_SOURCE = "my-reviewed-score.mei"\nSHOW_VEROVIO_WARNINGS = True\n']
    destination.write_text(json.dumps(edited))
    before = destination.read_bytes()
    template['cells'][3]['source'].append('NEW_UPSTREAM_OPTION = True\n')
    source.write_text(json.dumps(template))
    # Direct backup writes into a test corpus rather than the working repository.
    test_root = tmp_path / 'corpus'
    (test_root / 'validation').mkdir(parents=True)
    (test_root / 'validation/works.json').write_bytes((ROOT / 'validation/works.json').read_bytes())
    sync.sync_viewer(checkout=checkout, corpus_root=test_root, output=destination)
    updated = json.loads(destination.read_text())
    config = next(c for c in updated['cells'] if c['id'] == 'viewer-configuration')
    assert 'ZONE_OPACITY = 0.4' in ''.join(config['source'])
    assert 'NEW_UPSTREAM_OPTION = True' in ''.join(config['source'])
    configured = next(c for c in updated['cells'] if c['id'] == 'ddt-viewer-source')
    assert 'my-reviewed-score.mei' in ''.join(configured['source'])
    assert next((test_root / 'validation/viewer-backups').iterdir()).read_bytes() == before
    assert all(c.get('outputs', []) == [] for c in updated['cells'])
    assert updated['metadata']['ddt_camat_sync']['source_path'] == 'notebooks/mei_facsimile_viewer.ipynb'
    assert 'setup_camat' not in ''.join(next(c for c in updated['cells'] if c['id'] == 'viewer-path-setup')['source'])


def test_viewer_sync_from_a_ref_ignores_local_edits_and_strips_run_metadata(tmp_path):
    import subprocess
    sync = module('sync_camat_viewer')
    checkout = tmp_path / 'camat'
    source = checkout / 'notebooks/mei_facsimile_viewer.ipynb'
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps(viewer_template()))
    def git(*args):
        return subprocess.run(['git', '-C', str(checkout), *args], check=True,
                              capture_output=True, text=True).stdout.strip()
    git('init', '-q')
    git('add', '.')
    git('-c', 'user.name=Test', '-c', 'user.email=test@example.org', 'commit', '-qm', 'viewer')
    git('tag', 'v9.9.9')
    local = viewer_template()
    local['cells'][3]['source'].append('LOCAL_ONLY = True\n')
    local['cells'][3]['metadata']['execution'] = {'iopub.status.idle': '2026-10-21T12:00:00Z'}
    local['metadata']['widgets'] = {'application/vnd.jupyter.widget-state+json': {'state': {}}}
    source.write_text(json.dumps(local))
    released = tmp_path / 'released.ipynb'
    sync.sync_viewer(checkout=checkout, output=released, ref='v9.9.9')
    assert 'LOCAL_ONLY' not in released.read_text()
    provenance = json.loads(released.read_text())['metadata']['ddt_camat_sync']
    assert (provenance['git_ref'], provenance['git_commit']) == ('v9.9.9', git('rev-parse', 'HEAD'))
    assert 'git_status' not in provenance
    working = json.loads(sync.sync_viewer(checkout=checkout, output=tmp_path / 'working.ipynb').read_text())
    assert 'LOCAL_ONLY' in json.dumps(working)
    assert 'widgets' not in working['metadata']
    assert all('execution' not in c['metadata'] for c in working['cells'])
    assert working['metadata']['ddt_camat_sync']['git_status'] == 'M notebooks/mei_facsimile_viewer.ipynb'
    with pytest.raises(ValueError, match='Unknown CAMAT Git ref'):
        sync.sync_viewer(checkout=checkout, output=tmp_path / 'other.ipynb', ref='v0.0.0')


def test_viewer_dry_run_and_unmanaged_file_are_safe(tmp_path):
    sync = module('sync_camat_viewer')
    checkout = tmp_path / 'camat'
    source = checkout / 'notebooks/mei_facsimile_viewer.ipynb'
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps(viewer_template()))
    output = tmp_path / 'viewer.ipynb'
    sync.sync_viewer(checkout=checkout, output=output, dry_run=True)
    assert not output.exists()
    output.write_text(json.dumps(viewer_template()))
    before = output.read_bytes()
    with pytest.raises(ValueError, match='not a managed'):
        sync.sync_viewer(checkout=checkout, output=output)
    assert output.read_bytes() == before


def test_update_helper_targets_running_python_and_explicit_ref(monkeypatch):
    import sys
    update = module('update_camat')
    monkeypatch.setattr(update.importlib.util, 'find_spec', lambda name: object())
    command = update.update_commands(git_ref='v0.2.7')[0]
    assert command[0] == sys.executable
    assert '--force-reinstall' in command
    assert 'camat[notebooks,validation]' in command[-1]
    assert command[-1].endswith('@v0.2.7')
    with pytest.raises(ValueError, match='existing local'):
        update.update_commands(git_ref='main', pull=True)


def test_update_helper_uses_uv_pip_when_the_python_has_no_pip(monkeypatch):
    import sys
    update = module('update_camat')
    monkeypatch.setattr(update.importlib.util, 'find_spec', lambda name: None)
    monkeypatch.setattr(update.shutil, 'which', lambda name: '/opt/bin/uv')
    command = update.update_commands(git_ref='v0.2.7')[0]
    assert command[:5] == ['/opt/bin/uv', 'pip', 'install', '--python', sys.executable]
    assert update.pip_command('check') == ['/opt/bin/uv', 'pip', 'check', '--python', sys.executable]
    monkeypatch.setattr(update.shutil, 'which', lambda name: None)
    with pytest.raises(ValueError, match='no pip module'):
        update.pip_command('check')


def test_local_update_refuses_to_pull_a_dirty_checkout(tmp_path, monkeypatch):
    from types import SimpleNamespace
    update = module('update_camat')
    (tmp_path / 'camat').mkdir()
    (tmp_path / 'camat/mei_validation.py').touch()
    (tmp_path / '.git').mkdir()
    monkeypatch.setattr(update.subprocess, 'run', lambda *a, **kw: SimpleNamespace(stdout=' M camat/mei_validation.py\n'))
    with pytest.raises(ValueError, match='Commit or stash'):
        update.update_commands(checkout=tmp_path, pull=True)


def test_corpus_notebook_is_thin_and_runs_off_by_default():
    notebook = json.loads((ROOT / 'mei_corpus_checks.ipynb').read_text())
    sources = [''.join(cell['source']) for cell in notebook['cells'] if cell['cell_type'] == 'code']
    assert any('RUN_CHECKS = False' in source for source in sources)
    assert any('corpus.run_corpus_validation(' in source for source in sources)
    assert not any('pip", "install' in source or 'edition_rows(' in source for source in sources)
    for source in sources:
        compile(source, '<corpus notebook>', 'exec')
