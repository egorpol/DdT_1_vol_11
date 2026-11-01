"""Run the browser-independent player and notation mapping contracts in node."""
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which('node') is None, reason='node is not installed')
def test_tempo_javascript():
    result = subprocess.run(['node', '--test', 'tests/js/'], cwd=Path(__file__).resolve().parents[1],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    assert result.returncode == 0, result.stdout
