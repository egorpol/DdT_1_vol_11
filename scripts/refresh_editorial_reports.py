#!/usr/bin/env python3
"""Refresh tracked, per-score editorial CSVs with current CAMAT and DdT checks."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import signal
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_corpus import corpus_exit_code, plan_corpus_validation

COLUMNS = ['severity', 'category', 'origin', 'check', 'file', 'line', 'element',
           'xml_id', 'measure_n', 'staff_n', 'layer_n', 'message', 'expected', 'actual', 'context']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def report_path(root, work):
    source = Path(root) / work['file']
    return source.with_name(source.stem + '_consistency_report.csv')


def editorial_rows(result, work, root):
    """Keep validator findings intact, with portable paths and source locations."""
    from lxml import etree
    root = Path(root).resolve()
    source = root / work['file']
    ids = {}
    try:
        tree = etree.parse(str(source), etree.XMLParser(collect_ids=False))
        for element in tree.iter():
            value = element.get('{http://www.w3.org/XML/1998/namespace}id')
            if value:
                ids.setdefault(value, element)
    except (OSError, etree.XMLSyntaxError):
        pass  # Parse failures are already findings; retain their report.
    rows = []
    for finding in result.findings:
        row = {name: finding.get(name, '') for name in COLUMNS}
        row['file'] = row['file'] or work['file']  # One score per validation run.
        row['origin'] = row['origin'] or 'CAMAT'
        for name, value in row.items():
            if isinstance(value, str):
                row[name] = value.replace(str(root) + '/', '').replace(str(root), '.')
            elif value is None:
                row[name] = ''
        element = ids.get(row['xml_id'])
        if element is not None:
            if not row['line']:
                row['line'] = element.sourceline or ''
            if not row['element']:
                row['element'] = etree.QName(element).localname
            for ancestor in [element, *element.iterancestors()]:
                name = etree.QName(ancestor).localname
                column = {'measure': 'measure_n', 'staff': 'staff_n', 'layer': 'layer_n'}.get(name)
                if column and not row[column]:
                    row[column] = ancestor.get('n', '')
        rows.append(row)
    def order(row):
        line = str(row['line'])
        return ({'error': 0, 'warning': 1, 'info': 2}.get(row['severity'], 3),
                int(line) if line.isdigit() else 0, row['check'], row['xml_id'])
    return sorted(rows, key=order)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def validate_work(work, *, root, manifest, output, check_network):
    """Contain native failures in a worker; retain evidence of a failed consumer."""
    directory = output / work['key']
    directory.mkdir(parents=True, exist_ok=True)
    # A worker failing before its first checkpoint must never reuse old results.
    for name in ['run.json', 'findings.json', 'general/run.json']:
        (directory / name).unlink(missing_ok=True)
    arguments = [sys.executable, str(root / 'scripts/validate_corpus.py'),
                 '--manifest', str(manifest), '--work', work['key'], '--mode', 'review',
                 '--output-dir', str(directory), '--verovio', '--camat-parse',
                 '--editorial-diagnostics', '--group-diagnostics']
    if check_network:
        arguments.append('--network')
    with (directory / 'worker.log').open('w', encoding='utf-8') as log:
        process = subprocess.run(arguments, cwd=root, stdout=log, stderr=subprocess.STDOUT)
    if not (directory / 'run.json').is_file():
        raise RuntimeError(f'{work["key"]}: worker produced no new run record; inspect {directory / "worker.log"}. Shared reports retained.')
    record = json.loads((directory / 'run.json').read_text())
    recovered = None
    if record.get('completion_status') != 'completed':
        progress_path = directory / 'general/run.json'
        progress = json.loads(progress_path.read_text()) if progress_path.is_file() else {}
        if process.returncode >= 0 or progress.get('active_check') != 'camat_parse':
            raise RuntimeError(f'{work["key"]}: worker exited {process.returncode}; inspect {directory / "worker.log"}. Shared reports retained.')
        # This observed native parser failure cannot be caught inside Python.
        # Rerun every other check, preserving the crashed attempt and its signal.
        archive = directory.with_name(directory.name + '-crashed-attempt')
        if archive.exists():
            archive = archive.with_name(archive.name + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        directory.rename(archive)
        directory.mkdir()
        arguments.remove('--camat-parse')
        with (directory / 'worker.log').open('w', encoding='utf-8') as log:
            retry = subprocess.run(arguments, cwd=root, stdout=log, stderr=subprocess.STDOUT)
        record = json.loads((directory / 'run.json').read_text())
        if record.get('completion_status') != 'completed':
            raise RuntimeError(f'{work["key"]}: recovery worker exited {retry.returncode}; shared reports retained.')
        recovered = (signal.Signals(-process.returncode).name, archive.relative_to(root).as_posix())
    findings = json.loads((directory / 'findings.json').read_text())
    if recovered:
        native_signal, evidence = recovered
        message = (f'CAMAT consumer parsing terminated with {native_signal}. All other checks were rerun '
                   f'in a fresh process; CAMAT parsing remains incomplete. Crash evidence: {evidence}/worker.log.')
        findings.append({'severity': 'error', 'category': 'execution', 'origin': 'CAMAT',
                         'check': 'camat_parse_native_crash', 'file': work['file'], 'message': message})
        record['executions']['camat_parse'] = {
            'requested': True, 'required': False, 'status': 'execution-error', 'running': False,
            'findings_count': 1, 'reason': message, 'native_signal': native_signal,
            'recovery': 'Other checks rerun with consumer parsing disabled.',
        }
        record['options']['check_camat_parse'] = True
        record['consumer_diagnostics'] = 'incomplete'
        record['native_crash_recovery'] = {'signal': native_signal, 'evidence_directory': evidence}
        (directory / 'run.json').write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n')
        (directory / 'findings.json').write_text(json.dumps(findings, indent=2, ensure_ascii=False) + '\n')
        write_csv(directory / 'findings.csv', [{key: row.get(key, '') for key in COLUMNS} for row in findings])
    return SimpleNamespace(record=record, findings=findings,
                           passed=record['conformance'] == record['required_checks_status'] == 'passed')


def refresh_reports(*, root=ROOT, manifest=None, output_dir=None, check_network=False):
    """Validate all editorial selections before replacing the shared report set.

    Validation errors remain in refreshed reports and return exit code 1.
    An interrupted/raised validation leaves the previous shared report set intact.
    """
    root = Path(root).resolve()
    manifest = Path(manifest or root / 'validation/editorial-works.json').resolve()
    output = Path(output_dir or root / 'validation/runs/editorial').resolve()
    plan = plan_corpus_validation(root=root, manifest=manifest, mode='review', output_dir=output)
    if plan['unlisted_files']:
        raise ValueError('Add all assembled work-directory MEI to the editorial list before refreshing reports: '
                         + ', '.join(str(p.relative_to(root)) for p in plan['unlisted_files']))
    before = {path: digest(path) for path in plan['files']}
    if any(not (root / work['file']).is_file() for work in plan['works']):
        raise ValueError('Editorial work list contains a missing score.')
    completed = []
    identity = None
    failed = False
    for index, work in enumerate(plan['works'], 1):
        print(f'[{index}/{len(plan["works"])}] {work["key"]}', flush=True)
        result = validate_work(work, root=root, manifest=manifest, output=output, check_network=check_network)
        camat = {key: result.record['camat'].get(key) for key in
                 ('module_version', 'distribution_version', 'git_branch', 'git_commit', 'source_tree_sha256')}
        camat['working_tree_dirty'] = bool(result.record['camat'].get('git_status'))
        if identity is not None and identity != camat:
            raise RuntimeError('CAMAT changed during refresh; previous shared reports retained.')
        identity = camat
        rows = editorial_rows(result, work, root)
        destination = report_path(root, work)
        staged = output / 'export' / destination.name
        write_csv(staged, rows)
        record = result.record
        if any(item['sha256_before'] != before[Path(item['path'])] for item in record['inputs']):
            raise RuntimeError('Worker input hashes differ from this refresh; previous shared reports retained.')
        entry = {
            'work_key': work['key'], 'input_file': work['file'], 'input_sha256': before[root / work['file']],
            'report_file': destination.relative_to(root).as_posix(), 'report_sha256': digest(staged),
            'completion_status': record['completion_status'],
            'mei_conformance': record['mei_conformance'], 'consumer_diagnostics': record['consumer_diagnostics'],
            'ddt_publication_acceptance': record['ddt']['publication_acceptance'],
            'input_unchanged': all(item['unchanged'] for item in record['inputs']),
            'findings': dict(Counter(row['severity'] for row in rows)),
            'checks': {name: {key: value for key, value in execution.items()
                             if key in {'requested', 'required', 'status', 'findings_count', 'reason'}}
                       for name, execution in record['executions'].items()},
        }
        completed.append((destination, staged, entry))
        failed = bool(corpus_exit_code(result)) or entry['consumer_diagnostics'] != 'passed' or failed
        print(f'  MEI: {entry["mei_conformance"]}; consumers: {entry["consumer_diagnostics"]}; '
              f'DdT: {entry["ddt_publication_acceptance"]}; findings: {len(rows)}', flush=True)
    if any(digest(path) != checksum for path, checksum in before.items()):
        raise RuntimeError('MEI changed during refresh; previous shared reports retained.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    summary_path = root / 'validation/editorial-reports.json'
    backup = root / 'validation/report-backups' / stamp
    backup.mkdir(parents=True, exist_ok=True)
    for destination in [*(p for p, _, _ in completed), summary_path]:
        if destination.exists():
            shutil.copy2(destination, backup / destination.name)
    summary = {
        'format_version': 1, 'completed_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'Shared editorial findings for all assembled works; not publication sign-off.',
        'camat': identity, 'dependency_versions': record['dependency_versions'],
        'schema': {'file': plan['schema'].relative_to(root).as_posix(), 'sha256': digest(plan['schema'])},
        'sources': {p.relative_to(root).as_posix(): digest(p) for p in
                    [manifest, plan['profile_path'], root / 'validation/rules.py',
                     root / 'scripts/validate_corpus.py', root / 'scripts/refresh_editorial_reports.py']},
        'options': record['options'], 'works': [entry for _, _, entry in completed],
    }
    for destination, staged, _ in completed:
        shutil.copyfile(staged, destination)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Refreshed {len(completed)} tracked editorial reports. Provenance: validation/editorial-reports.json', flush=True)
    return int(failed)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'validation/editorial-works.json')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'validation/runs/editorial')
    parser.add_argument('--network', action='store_true', help='Also fetch/check HTTP image targets.')
    args = parser.parse_args(argv)
    return refresh_reports(manifest=args.manifest, output_dir=args.output_dir, check_network=args.network)


if __name__ == '__main__':
    raise SystemExit(main())
