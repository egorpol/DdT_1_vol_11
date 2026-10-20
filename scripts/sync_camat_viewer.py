#!/usr/bin/env python3
"""Refresh the corpus viewer notebook from a local CAMAT checkout."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKOUT = ROOT.parents[1] / 'camat_v2'


def _source(cell):
    value = cell['source']
    return ''.join(value) if isinstance(value, list) else value


def _set_source(cell, source):
    cell['source'] = source.splitlines(keepends=True)


def _assignments(source):
    return {node.targets[0].id: ast.get_source_segment(source, node)
            for node in ast.parse(source).body if isinstance(node, ast.Assign)
            and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}


def build_viewer_notebook(source, *, corpus_root=ROOT, existing=None):
    """Keep CAMAT viewer cells, adapt setup/input, preserve recognized user options."""
    notebook = copy.deepcopy(source)
    cells = notebook['cells']
    setup = next((c for c in cells if c.get('id') == 'viewer-path-setup'), None)
    config = next((c for c in cells if c.get('id') == 'viewer-configuration'), None)
    sources = [c for c in cells if c['cell_type'] == 'code' and 'MEI_SOURCE' in _assignments(_source(c))]
    if setup is None or config is None or len(sources) != 1:
        raise ValueError('CAMAT viewer layout changed; review its setup/configuration cells before adapting.')
    source_cell = sources[0]
    source_cell['id'] = 'ddt-viewer-source'
    _set_source(cells[0], '''# Inspect DdT notation and facsimiles

This notebook is refreshed from CAMAT by `python scripts/sync_camat_viewer.py`.
Rendering, annotations and watching use the installed CAMAT package. Updates
preserve recognized configuration assignments and back up the previous notebook.
It reads MEI without rewriting it. This viewer is an inspection tool; run
`mei_corpus_checks.ipynb` or `scripts/validate_corpus.py` for general + DdT checks.

Run from this repository, select the CAMAT Python kernel, and configure
`MEI_SOURCE` below. No package installation or tutorial download occurs here.
''')
    _set_source(setup, '''from pathlib import Path
import camat
from camat import launch_interactive_facsimile_viewer, read_facsimile_model

CORPUS_ROOT = next((p for p in (Path.cwd().resolve(), *Path.cwd().resolve().parents)
                    if (p / "validation/works.json").is_file()), None)
if CORPUS_ROOT is None:
    raise FileNotFoundError("Start this notebook from the DdT_1_vol_11 repository.")
print("CAMAT:", camat.__version__, camat.__file__)
print("Corpus:", CORPUS_ROOT)
''')
    manifest = json.loads((Path(corpus_root) / 'validation/works.json').read_text(encoding='utf-8'))
    if not manifest.get('works'):
        raise ValueError('Select a viewer example in validation/works.json first.')
    example = manifest['works'][0]['file']
    _set_source(source_cell,
        '# Choose a corpus-relative path or another supported CAMAT source.\n'
        f'MEI_SOURCE = str(CORPUS_ROOT / {example!r})\n'
        'SHOW_VEROVIO_WARNINGS = False\n')
    if existing is not None:
        old_cells = {c.get('id'): c for c in existing['cells']}
        for cell in (source_cell, config):
            old = old_cells.get(cell['id'])
            if old is None:
                continue
            previous = _assignments(_source(old))
            current = _source(cell)
            # Retain values for still-supported assignments; new upstream options
            # get their defaults. Never execute the user's configuration here.
            for node in reversed(ast.parse(current).body):
                if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                    continue
                replacement = previous.get(node.targets[0].id)
                if replacement is not None:
                    lines = current.splitlines(keepends=True)
                    lines[node.lineno - 1:node.end_lineno] = [replacement + '\n']
                    current = ''.join(lines)
            _set_source(cell, current)
    notebook.get('metadata', {}).pop('widgets', None)
    for cell in cells:
        cell.get('metadata', {}).pop('execution', None)
        if cell['cell_type'] == 'code':
            cell['execution_count'], cell['outputs'] = None, []
            compile(_source(cell), '<viewer cell>', 'exec')
    return notebook


def sync_viewer(*, checkout=DEFAULT_CHECKOUT, corpus_root=ROOT, output=None, dry_run=False, ref=None):
    checkout, corpus_root = Path(checkout).expanduser().resolve(), Path(corpus_root).resolve()
    source_path = checkout / 'notebooks/mei_facsimile_viewer.ipynb'
    output = Path(output or corpus_root / 'mei_facsimile_viewer.ipynb').resolve()
    if output == source_path:
        raise ValueError('Output must not overwrite the CAMAT source notebook.')
    def git(*args):
        run = subprocess.run(['git', '-C', str(checkout), *args], text=True, capture_output=True)
        return run.stdout.strip() if run.returncode == 0 else None
    relative = source_path.relative_to(checkout).as_posix()
    if ref is None:
        original = source_path.read_bytes()
    else:
        # A ref ignores local edits in the checkout's working copy of the notebook.
        commit = git('rev-parse', '--verify', '--quiet', f'{ref}^{{commit}}')
        if not commit:
            raise ValueError(f'Unknown CAMAT Git ref: {ref}')
        run = subprocess.run(['git', '-C', str(checkout), 'show', f'{commit}:{relative}'], capture_output=True)
        if run.returncode:
            raise ValueError(f'{relative} is not in CAMAT {ref}.')
        original = run.stdout
    source = json.loads(original)
    existing = json.loads(output.read_text(encoding='utf-8')) if output.exists() else None
    if existing is not None and 'ddt_camat_sync' not in existing.get('metadata', {}):
        raise ValueError('Existing viewer is not a managed CAMAT copy; archive or rename it before syncing.')
    notebook = build_viewer_notebook(source, corpus_root=corpus_root, existing=existing)
    provenance = {'source_path': relative, 'source_sha256': hashlib.sha256(original).hexdigest()}
    if ref is None:
        provenance.update(git_commit=git('rev-parse', 'HEAD'), git_branch=git('branch', '--show-current'),
                          git_status=git('status', '--porcelain', '--untracked-files=normal'))
    else:
        provenance.update(git_ref=ref, git_commit=commit)
    provenance['adapter_version'] = 1
    notebook.setdefault('metadata', {})['ddt_camat_sync'] = provenance
    content = (json.dumps(notebook, indent=1, ensure_ascii=False) + '\n').encode('utf-8')
    print('CAMAT viewer source:', source_path if ref is None else f'{ref}:{relative}')
    print('Source revision:', provenance.get('git_branch', ref), provenance['git_commit'])
    print('Corpus notebook:', output)
    if dry_run:
        print('Dry run; no notebook written.')
        return output
    if output.exists() and output.read_bytes() == content:
        print('Already synchronized.')
        return output
    if output.exists():
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = corpus_root / 'validation/viewer-backups' / f'{stamp}-{output.name}'
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output, backup)
        print('Previous notebook backup:', backup)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.ipynb.tmp')
    temporary.write_bytes(content)
    temporary.replace(output)
    print('Viewer refreshed. This copies the notebook; it does not update the installed CAMAT package.')
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, default=DEFAULT_CHECKOUT)
    parser.add_argument('--output', type=Path, help='Default: corpus-root mei_facsimile_viewer.ipynb.')
    parser.add_argument('--ref', help="Read the notebook from this CAMAT Git ref (e.g. v0.2.7), not the checkout's working file.")
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        sync_viewer(checkout=args.checkout, output=args.output, dry_run=args.dry_run, ref=args.ref)
    except (ValueError, OSError, KeyError, SyntaxError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
