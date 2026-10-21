#!/usr/bin/env python3
"""Run installed CAMAT's read-only MEI checks, then explicit DdT publication rules."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # Corpus rules only; CAMAT comes from the environment.
from validation.rules import edition_rows


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_blob(root, revision, file):
    """Bytes of a corpus-relative file at a Git revision, or None."""
    command = subprocess.run(['git', '-C', str(root), 'cat-file', 'blob', revision + ':./' + file], capture_output=True)
    return command.stdout if command.returncode == 0 else None


def _checkpoint(path, record):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def plan_corpus_validation(*, root=ROOT, manifest=None, profile=None, work_keys=None,
                           mode='review', output_dir=None):
    """Inspect explicit input selection without executing validators or writing files.

    Unlisted work-directory MEI is inventory, never selected implicitly.
    This function and ``run_corpus_validation`` are also used by the notebook.
    """
    root = Path(root).resolve()
    if mode not in {'review', 'release'}:
        raise ValueError('mode must be review or release')
    manifest_path = Path(manifest or root / 'validation/works.json').resolve()
    profile_path = Path(profile or root / 'validation/profile.json').resolve()
    manifest_data = json.loads(manifest_path.read_text(encoding='utf-8'))
    profile_data = json.loads(profile_path.read_text(encoding='utf-8'))
    if mode == 'release' and manifest_data.get('review_only'):
        raise ValueError('This editorial work list is review-only; use the publication manifest for release.')
    works = manifest_data.get('works')
    if not isinstance(works, list) or not works or any(not isinstance(w, dict) for w in works):
        raise ValueError('Work list must be nonempty and contain work records.')
    keys = [work.get('key') for work in works]
    if any(not isinstance(key, str) or not key for key in keys) or len(keys) != len(set(keys)):
        raise ValueError('Work list must have nonempty unique edition keys.')
    selected = set(keys if work_keys is None else work_keys)
    if not selected:
        raise ValueError('Select at least one work; an empty selection cannot pass.')
    if selected - set(keys):
        raise ValueError('Unknown work keys: ' + ', '.join(sorted(selected - set(keys))))
    files, directories = [], set()
    for work in works:
        for field in ('file', 'final_file'):
            value = work.get(field)
            if not isinstance(value, str) or not value:
                raise ValueError(f'{work["key"]}: missing {field}')
            path = (root / value).resolve()
            if not path.is_relative_to(root) or path.suffix != '.mei':
                raise ValueError('Manifest MEI paths must stay inside this corpus.')
        directories.add((root / work['file']).parent)
        files.append((root / work['file']).resolve())
    if len(files) != len(set(files)):
        raise ValueError('Each manifest work must select a distinct MEI file.')
    schema = (root / profile_data['schema']).resolve()
    if not schema.is_relative_to(root):
        raise ValueError('The edition schema must stay inside this corpus.')
    chosen = [work for work in works if work['key'] in selected]
    output = Path(output_dir or root / 'validation/runs/latest').resolve()
    chosen_files = [(root / work['file']).resolve() for work in chosen]
    if any(path == output or output in path.parents for path in chosen_files):
        raise ValueError('Report output must not contain selected input MEI files.')
    inventory = {path.resolve() for directory in directories for path in directory.glob('*.mei')}
    return {
        'root': root, 'mode': mode, 'manifest_path': manifest_path,
        'profile_path': profile_path, 'manifest': manifest_data, 'profile': profile_data,
        'schema': schema, 'works': chosen, 'files': chosen_files, 'output_dir': output,
        'unlisted_files': sorted(inventory - set(files)),
    }


def _corpus_identity(root):
    def git(*arguments):
        command = subprocess.run(['git', '-C', str(root), *arguments], text=True, capture_output=True)
        return command.stdout.strip() if command.returncode == 0 else None
    return {'root': str(root), 'git_commit': git('rev-parse', 'HEAD'),
            'git_branch': git('branch', '--show-current'),
            'git_status': git('status', '--porcelain', '--untracked-files=normal')}


def _publication_rows(plan, result):
    root, profile, manifest, mode = (plan[name] for name in ('root', 'profile', 'manifest', 'mode'))
    rows = []
    def add(check, message, *, file=None, severity='error'):
        row = {'severity': severity, 'category': 'ddt_publication', 'origin': profile['id'],
               'check': 'ddt.' + check, 'message': message}
        if file is not None:
            row['file'] = file
        rows.append(row)
    if result.record['schema']['sha256'] != profile['schema_sha256']:
        add('schema_hash', 'Local official schema differs from the recorded edition profile.')
    warnings = [row for row in result.findings
                if row.get('category') == 'schematron' and row.get('severity') == 'warning']
    if warnings and profile.get('reject_schematron_warnings_on_release'):
        add('schematron_warnings',
            f'{len(warnings)} official Schematron warning(s) remain pending publication review; no waiver is configured.',
            severity='error' if mode == 'release' else 'warning')
    if mode == 'release':
        reference = manifest.get('immutable_git_ref')
        if reference:
            exists = subprocess.run(['git', '-C', str(root), 'cat-file', '-e', reference + '^{commit}'], capture_output=True)
            if exists.returncode != 0:
                add('immutable_commit', 'Declared immutable corpus commit is not available locally for verification.')
            else:
                # Only the selected MEI is compared; the manifest cannot hold its own commit.
                # The MEI names the release tag instead, so the tag must carry the same bytes.
                tag = 'refs/tags/v' + str(manifest.get('release_version'))
                tagged = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', '-q', tag + '^{commit}'],
                                        capture_output=True).returncode == 0
                if not tagged:
                    add('release_tag', f'Release tag {tag.removeprefix("refs/tags/")} is not available locally; tag the manifest commit before release validation.')
                for work in plan['works']:
                    path = root / work['file']
                    blob = _git_blob(root, reference, work['file'])
                    if blob is None or not path.is_file() or blob != path.read_bytes():
                        add('immutable_content', 'Selected MEI differs from its copy at the declared immutable commit.',
                            file=work['file'])
                    if tagged and _git_blob(root, tag, work['file']) != blob:
                        add('release_tag', 'The release tag carries a different MEI than the declared immutable commit.',
                            file=work['file'])
        if not (root / 'CITATION.cff').is_file():
            add('citation', 'Release requires corpus CITATION.cff.')
        if manifest.get('release_scope') != 'mei-data-only':
            add('release_scope', 'This validator supports explicit MEI-data-only releases; image redistribution needs a separate inventory/rights gate.')
        for work in plan['works']:
            path = root / work['file']
            if not path.is_file() or work.get('sha256') != _digest(path):
                add('release_hash', 'Release work list must record the actual final MEI hash.', file=work['file'])
    for work in plan['works']:
        rows.extend(edition_rows(work, root_dir=root, profile=profile, manifest=manifest, mode=mode))
    return rows


def run_corpus_validation(*, root=ROOT, manifest=None, profile=None, work_keys=None,
                          mode='review', output_dir=None, check_verovio=False,
                          check_camat_parse=False, parsing_backend='verovio',
                          check_network=False, check_schematron=True, check_ppq=True,
                          check_editorial_diagnostics=False, check_group_diagnostics=False):
    """Return CAMAT's ValidationResult with DdT findings and run metadata.

    No installation, Git pull, notebook execution or MEI transformation occurs.
    Review accepts working filenames; release forces the configured consumers.
    Optional consumer/network failures remain separate from conformance.
    """
    from camat.mei_validation import DEFAULT_REQUIRED, run_mei_validation
    plan = plan_corpus_validation(root=root, manifest=manifest, profile=profile,
                                 work_keys=work_keys, mode=mode, output_dir=output_dir)
    root, profile_data, manifest_data = (plan[name] for name in ('root', 'profile', 'manifest'))
    output = plan['output_dir']
    output.mkdir(parents=True, exist_ok=True)
    _checkpoint(output / 'run.json', {
        'completion_status': 'running', 'mei_conformance': 'incomplete',
        'conformance': 'incomplete', 'consumer_diagnostics': 'incomplete',
        'ddt': {'mode': mode, 'publication_acceptance': 'incomplete', 'active_check': 'general'},
        'general_progress_record': str(output / 'general/run.json'),
    })
    required = profile_data['required_release_checks'] if mode == 'release' else DEFAULT_REQUIRED
    result = run_mei_validation(
        plan['files'], root=root, output_dir=output / 'general', schema=plan['schema'],
        profile='MEI-5.1-CMN', document_mode='standalone', check_ppq=check_ppq,
        check_schematron=check_schematron, check_verovio=check_verovio or mode == 'release',
        check_camat_parse=check_camat_parse or mode == 'release',
        parsing_backend=parsing_backend, check_network=check_network, required_checks=required,
        editorial_diagnostics=check_editorial_diagnostics, group_diagnostics=check_group_diagnostics,
    )
    result.record['completion_status'] = 'running'
    result.record['ddt'] = {'mode': mode, 'publication_acceptance': 'incomplete', 'active_check': 'publication'}
    result.write(output)
    policy_completed = True
    try:
        edition = _publication_rows(plan, result)
    except Exception as exc:
        policy_completed = False
        edition = [{'severity': 'error', 'category': 'execution', 'origin': profile_data['id'],
                    'check': 'ddt.policy_execution', 'message': f'{type(exc).__name__}: {exc}'}]
    # Hashes cover the entire shared + corpus run, including the local policy pass.
    for item in result.record['inputs']:
        path = Path(item['path'])
        item['sha256_after'] = _digest(path) if path.is_file() else None
        item['unchanged'] = item['sha256_before'] is not None and item['sha256_before'] == item['sha256_after']
    if any(not item['unchanged'] for item in result.record['inputs']):
        result.record['executions']['input_hashes']['status'] = 'failed'
        result.record['conformance'] = result.record['required_checks_status'] = 'failed'
        edition.append({'severity': 'error', 'category': 'ddt_publication', 'origin': profile_data['id'],
                        'check': 'ddt.input_changed', 'message': 'Selected input disappeared or changed during the corpus run.'})
    hard_errors = any(row['severity'] == 'error' for row in edition)
    if not policy_completed:
        acceptance = 'incomplete'
    elif hard_errors:
        acceptance = 'failed'
    elif not result.passed:
        acceptance = 'failed' if 'failed' in {result.record['conformance'], result.record['required_checks_status']} else 'incomplete'
    elif mode == 'release':
        acceptance = 'passed'
    else:
        acceptance = 'needs-review' if edition else 'review-clean'
    result.findings.extend(edition)
    result.record['mei_conformance'] = result.record['conformance']
    result.record['ddt'] = {
        'mode': mode, 'profile_id': profile_data['id'], 'profile_version': profile_data['profile_version'],
        'profile_path': str(plan['profile_path']), 'profile_sha256': _digest(plan['profile_path']),
        'manifest_path': str(plan['manifest_path']), 'manifest_sha256': _digest(plan['manifest_path']),
        'rule_code_sha256': _digest(root / 'validation/rules.py'),
        'entry_point_sha256': _digest(Path(__file__)), 'corpus': _corpus_identity(root),
        'selected_work_keys': [work['key'] for work in plan['works']],
        'unlisted_work_files': [str(path.relative_to(root)) for path in plan['unlisted_files'] if path.is_relative_to(root)],
        'publication_acceptance': acceptance, 'publication_findings_count': len(edition),
        'policy_execution_status': 'completed' if policy_completed else 'execution-error',
        'scope': manifest_data.get('scope'), 'active_check': None,
    }
    result.record['completion_status'] = 'completed' if policy_completed else 'incomplete'
    result.write(output)
    return result


def corpus_exit_code(result):
    """Review needs-review is nonfatal; incomplete/failed checks never return zero."""
    acceptance = result.record['ddt']['publication_acceptance']
    return int(not result.passed or acceptance in {'failed', 'incomplete'} or
               (result.record['ddt']['mode'] == 'release' and acceptance != 'passed'))


def print_validation_summary(result, output_dir):
    print('MEI conformance:', result.record['mei_conformance'])
    print('Consumer diagnostics:', result.record['consumer_diagnostics'])
    print('DdT publication acceptance:', result.record['ddt']['publication_acceptance'])
    network = result.record['executions']['image_network']
    if network['status'] == 'not-applicable':
        print('Image network:', network['reason'])
    identity = result.record['camat']
    print('CAMAT module/distribution:', identity['module_version'], '/', identity.get('distribution_version'))
    print('CAMAT path:', identity['module_path'])
    print('CAMAT revision:', identity.get('git_branch'), identity.get('git_commit'))
    print('CAMAT source hash:', identity['source_tree_sha256'])
    print('Selected works:', ', '.join(result.record['ddt']['selected_work_keys']))
    print('Unlisted work-directory MEI (not checked):', len(result.record['ddt']['unlisted_work_files']))
    for label, name in [('Run JSON (checks, versions, hashes)', 'run.json'),
                        ('Findings CSV (general + DdT)', 'findings.csv'),
                        ('Findings JSON (same findings)', 'findings.json')]:
        print(label + ':', Path(output_dir).resolve() / name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('review', 'release'), default='review')
    parser.add_argument('--manifest', type=Path, default=ROOT / 'validation/works.json')
    parser.add_argument('--profile', type=Path, default=ROOT / 'validation/profile.json')
    parser.add_argument('--work', action='append', help='Manifest keys; default is the entire explicit list.')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'validation/runs/latest')
    parser.add_argument('--verovio', action='store_true', help='Full rendering in review (required for release).')
    parser.add_argument('--camat-parse', action='store_true', help='Consumer parsing in review (required for release).')
    parser.add_argument('--parsing-backend', default='verovio')
    parser.add_argument('--network', action='store_true', help='Optional HTTP image connectivity pass.')
    parser.add_argument('--skip-schematron', action='store_true', help='Diagnostic only; conformance stays incomplete.')
    parser.add_argument('--no-ppq', action='store_true', help='Disable written/PPQ comparison; never strip attributes.')
    parser.add_argument('--editorial-diagnostics', action='store_true', help='Additional duration/layer/term editorial diagnostics.')
    parser.add_argument('--group-diagnostics', action='store_true', help='Compare staff/term consistency within the selected files.')
    parser.add_argument('--list-works', action='store_true', help='Print the selected plan without validating.')
    args = parser.parse_args(argv)
    options = dict(manifest=args.manifest, profile=args.profile, work_keys=args.work,
                   mode=args.mode, output_dir=args.output_dir)
    try:
        plan = plan_corpus_validation(**options)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    if args.list_works:
        print('Scope:', plan['manifest'].get('scope'))
        for work in plan['works']:
            print(work['key'] + ':', work['file'])
        print('Unlisted work-directory MEI (not checked):', len(plan['unlisted_files']))
        return 0
    try:
        result = run_corpus_validation(**options, check_verovio=args.verovio,
            check_camat_parse=args.camat_parse, parsing_backend=args.parsing_backend,
            check_network=args.network, check_schematron=not args.skip_schematron,
            check_ppq=not args.no_ppq, check_editorial_diagnostics=args.editorial_diagnostics,
            check_group_diagnostics=args.group_diagnostics)
    except ImportError as exc:
        parser.error('Install the CAMAT checkout with its validation extra in this environment; see validation/README.md. ' + str(exc))
    print_validation_summary(result, args.output_dir)
    return corpus_exit_code(result)


if __name__ == '__main__':
    raise SystemExit(main())
