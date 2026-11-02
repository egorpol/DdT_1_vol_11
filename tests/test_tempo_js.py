"""Run the browser-independent player and notation mapping contracts in node."""
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which('node') is None, reason='node is not installed')
def test_tempo_javascript():
    root = Path(__file__).resolve().parents[1]
    # Name the files: node 22 (the CI runner's) reads a directory argument as a module path.
    files = sorted(str(path.relative_to(root)) for path in (root / 'tests' / 'js').glob('*.test.mjs'))
    assert files
    result = subprocess.run(['node', '--test', *files], cwd=root,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert result.returncode == 0, result.stdout
