#!/usr/bin/env python3
"""Explicitly update/install CAMAT for this corpus; never called by validation."""
from __future__ import annotations

import argparse
import importlib.util
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHECKOUT = ROOT.parents[1] / 'camat_v2'


def pip_command(subcommand):
    """pip of the running Python, or uv's pip for a uv environment without pip."""
    if importlib.util.find_spec('pip') is not None:
        return [sys.executable, '-m', 'pip', subcommand]
    uv = shutil.which('uv')
    if uv is None:
        raise ValueError('This Python has no pip module and uv is not on PATH.')
    return [uv, 'pip', subcommand, '--python', sys.executable]


def update_commands(*, checkout=DEFAULT_CHECKOUT, pull=False, git_ref=None):
    """Build commands for the same Python environment that invoked this helper."""
    if git_ref is not None:
        if pull:
            raise ValueError('--pull is for an existing local checkout; Git installation resolves its ref itself.')
        if not git_ref or any(c.isspace() for c in git_ref) or any(c in git_ref for c in '@?#'):
            raise ValueError('Supply a plain CAMAT Git branch, tag or commit.')
        return [[*pip_command('install'), '--upgrade', '--force-reinstall',
                 f'camat[notebooks,validation] @ git+https://github.com/egorpol/camat_v2.git@{git_ref}']]
    checkout = Path(checkout).expanduser().resolve()
    if not (checkout / 'camat/mei_validation.py').is_file():
        raise ValueError('Choose a CAMAT checkout containing camat/mei_validation.py.')
    commands = []
    if pull:
        if not (checkout / '.git').exists():
            raise ValueError('--pull requires a CAMAT Git checkout.')
        state = subprocess.run(['git', '-C', str(checkout), 'status', '--porcelain'],
                               text=True, capture_output=True, check=True)
        if state.stdout.strip():
            raise ValueError('Commit or stash CAMAT changes before --pull; this helper does not discard them.')
        commands.append(['git', '-C', str(checkout), 'pull', '--ff-only'])
    commands.append([*pip_command('install'), '-e', f'{checkout}[notebooks,validation]'])
    return commands


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, default=DEFAULT_CHECKOUT)
    parser.add_argument('--pull', action='store_true', help='Fast-forward the local checkout on its current branch before installing.')
    parser.add_argument('--git-ref', help='Instead install a snapshot from remote Git, e.g. v0.2.7 or main.')
    parser.add_argument('--dry-run', action='store_true', help='Print commands without installing/updating.')
    parser.add_argument('--status', action='store_true', help='Print installed CAMAT provenance only.')
    args = parser.parse_args(argv)
    if args.status:
        if args.pull or args.git_ref or args.dry_run:
            parser.error('--status cannot be combined with update options.')
    else:
        try:
            commands = update_commands(checkout=args.checkout, pull=args.pull, git_ref=args.git_ref)
        except (ValueError, OSError, subprocess.CalledProcessError) as exc:
            parser.error(str(exc))
        for command in commands:
            print(shlex.join(command), flush=True)
            if not args.dry_run:
                subprocess.run(command, check=True)
        if args.dry_run:
            return 0
    # A fresh process observes the installed code after pip has changed it.
    try:
        subprocess.run(pip_command('check'), check=True)
    except ValueError as exc:
        print('Dependency check skipped:', exc)
    subprocess.run([sys.executable, '-c',
        'import json; from camat import camat_provenance; print(json.dumps(camat_provenance(), indent=2))'], check=True)
    print('Install libxml2/xmllint separately. Restart notebook kernels after updates.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
