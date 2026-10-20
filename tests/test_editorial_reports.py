from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module():
    spec = importlib.util.spec_from_file_location('ddt_editorial', ROOT / 'scripts/refresh_editorial_reports.py')
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_editorial_list_covers_assembled_scores_without_expanding_release_scope():
    m = module()
    plan = m.plan_corpus_validation(manifest=ROOT / 'validation/editorial-works.json')
    assert len(plan['works']) == 16
    assert not plan['unlisted_files']
    assert plan['manifest']['review_only'] is True
    release_list = json.loads((ROOT / 'validation/works.json').read_text())
    assert len(release_list['works']) == 1
    appendix = [w for w in plan['works'] if w['kind'] == 'appendix']
    assert len(appendix) == 3
    assert all(w['opus'] is None for w in appendix)
    assert {w['key']: w['catalogue'] for w in appendix} == {
        'app_01_suite_to_op1_04': 'BuxWV 273',
        'app_02_sonata_2violins_gamba_cembalo_c_major': 'BuxWV 266',
        'app_03_sonata_gamba_violin_cembalo_d_major': 'BuxWV 267',
    }
    assert [len(w['staff_roles']) for w in appendix] == [5, 6, 5]
    assert all(set(w['staff_roles']) == {str(n) for n in range(1, len(w['staff_roles']) + 1)}
               and all(w['staff_roles'].values()) for w in appendix)
    assert [w['consulted_sources'] for w in appendix] == [
        ['src.ddt1903'], ['src.ddt1903', 'src.uppsala.buxwv266'], ['src.ddt1903'],
    ]


def test_review_only_manifest_cannot_be_used_for_release():
    m = module()
    with pytest.raises(ValueError, match='review-only'):
        m.plan_corpus_validation(manifest=ROOT / 'validation/editorial-works.json', mode='release')


def test_export_retains_global_execution_errors_and_locates_editorial_events(tmp_path):
    m = module()
    path = tmp_path / 'score.mei'
    path.write_text('<mei xmlns="http://www.music-encoding.org/ns/mei">\n'
                    '<music><measure n="12"><staff n="2"><layer n="1">\n'
                    '<note xml:id="n1"/>\n</layer></staff></measure></music></mei>')
    work = {'file': 'score.mei'}
    result = SimpleNamespace(findings=[
        {'severity': 'error', 'category': 'execution', 'check': 'schematron_execution', 'message': 'Missing validator'},
        {'severity': 'warning', 'origin': 'DdT_1_vol_11', 'check': 'ddt.event_ids',
         'xml_id': 'n1', 'file': str(path), 'message': 'Review event'},
    ])
    rows = m.editorial_rows(result, work, tmp_path)
    assert rows[0]['file'] == 'score.mei' and rows[0]['severity'] == 'error'
    event = rows[1]
    assert (event['line'], event['measure_n'], event['staff_n'], event['layer_n']) == (3, '12', '2', '1')
    destination = tmp_path / 'report.csv'
    m.write_csv(destination, rows)
    saved = list(csv.DictReader(destination.open()))
    assert saved[1]['origin'] == 'DdT_1_vol_11'
    assert str(tmp_path) not in destination.read_text()
    assert b'\r\n' not in destination.read_bytes()


def test_raised_validation_does_not_replace_existing_shared_reports(tmp_path, monkeypatch):
    m = module()
    path = tmp_path / 'score.mei'
    path.write_text('<mei/>')
    work = {'key': 'score', 'file': 'score.mei'}
    plan = {'works': [work], 'files': [path], 'unlisted_files': []}
    monkeypatch.setattr(m, 'plan_corpus_validation', lambda **kw: plan)
    def fail(*args, **kw):
        raise RuntimeError('validator crashed')
    monkeypatch.setattr(m, 'validate_work', fail)
    report = m.report_path(tmp_path, work)
    report.write_text('student working report\n')
    with pytest.raises(RuntimeError, match='validator crashed'):
        m.refresh_reports(root=tmp_path)
    assert report.read_text() == 'student working report\n'


def test_unlisted_work_is_not_silently_omitted(tmp_path, monkeypatch):
    m = module()
    monkeypatch.setattr(m, 'plan_corpus_validation', lambda **kw: {'unlisted_files': [tmp_path / 'new.mei']})
    with pytest.raises(ValueError, match='new.mei'):
        m.refresh_reports(root=tmp_path)


def test_native_consumer_crash_is_recorded_without_claiming_consumer_pass(tmp_path, monkeypatch):
    m = module()
    work = {'key': 'score', 'file': 'score.mei'}
    output = tmp_path / 'validation/runs/editorial'
    directory = output / 'score'
    calls = []
    def worker(arguments, **options):
        calls.append(arguments.copy())
        if len(calls) == 1:
            (directory / 'run.json').write_text('{"completion_status":"running"}')
            (directory / 'general').mkdir()
            (directory / 'general/run.json').write_text('{"active_check":"camat_parse"}')
            return SimpleNamespace(returncode=-11)
        record = {'completion_status': 'completed', 'conformance': 'passed', 'required_checks_status': 'passed',
                  'consumer_diagnostics': 'passed', 'executions': {'camat_parse': {'status': 'skipped'}},
                  'options': {'check_camat_parse': False}}
        (directory / 'run.json').write_text(json.dumps(record))
        (directory / 'findings.json').write_text('[]')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(m.subprocess, 'run', worker)
    result = m.validate_work(work, root=tmp_path, manifest=tmp_path / 'manifest.json',
                             output=output, check_network=False)
    assert result.passed
    assert result.record['consumer_diagnostics'] == 'incomplete'
    assert result.record['executions']['camat_parse']['status'] == 'execution-error'
    assert result.record['executions']['camat_parse']['requested'] is True
    assert result.findings[0]['check'] == 'camat_parse_native_crash'
    assert (output / 'score-crashed-attempt/worker.log').exists()
    assert '--camat-parse' in calls[0] and '--camat-parse' not in calls[1]


def test_worker_failure_cannot_reuse_a_previous_completed_run(tmp_path, monkeypatch):
    m = module()
    output = tmp_path / 'validation/runs/editorial'
    directory = output / 'score'
    directory.mkdir(parents=True)
    (directory / 'run.json').write_text('{"completion_status":"completed"}')
    (directory / 'findings.json').write_text('[]')
    monkeypatch.setattr(m.subprocess, 'run', lambda *a, **kw: SimpleNamespace(returncode=2))
    with pytest.raises(RuntimeError, match='no new run record'):
        m.validate_work({'key': 'score', 'file': 'score.mei'}, root=tmp_path,
                        manifest=tmp_path / 'manifest.json', output=output, check_network=False)
