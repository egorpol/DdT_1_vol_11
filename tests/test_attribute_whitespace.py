"""No MEI attribute value may start or end with whitespace.

The MEI RelaxNG schema accepts such values (token comparison collapses
whitespace), and Verovio reads ``accid="f "`` as a flat, but music21 rejects
the whole work on it. OMR left eight of them in the page files and the
assembled works; see the CHANGELOG entry of 2026-11-20.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]


def tracked_mei() -> list[Path]:
    out = subprocess.run(
        ['git', 'ls-files', '-z', '*.mei'],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return [ROOT / name for name in out.split('\0') if name]


def edge_whitespace(path: Path) -> list[str]:
    # Page files carry OMR duplicate ids; this check is not about ids.
    tree = etree.parse(str(path), etree.XMLParser(collect_ids=False))
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    return [
        f'{rel}:{el.sourceline} {etree.QName(el).localname}/@{etree.QName(name).localname}={value!r}'
        for el in tree.iter()
        if isinstance(el.tag, str)
        for name, value in el.attrib.items()
        if value != value.strip()
    ]


def test_tracked_mei_files_are_found():
    files = tracked_mei()
    assert any(p.parent.name == '11_buxtehude_sonatas_final' for p in files)
    assert len(files) > 100


def test_no_attribute_value_has_edge_whitespace():
    problems = [p for path in tracked_mei() for p in edge_whitespace(path)]
    assert not problems, '\n'.join(problems)


def test_edge_whitespace_is_detected(tmp_path):
    sample = tmp_path / 'sample.mei'
    sample.write_text(
        '<mei xmlns="http://www.music-encoding.org/ns/mei">'
        '<note xml:id=" n1" accid="f " dur.ppq="9\t" pname="e"/></mei>',
        encoding='utf-8',
    )
    found = edge_whitespace(sample)
    assert len(found) == 3, found
    assert any("@accid='f '" in line for line in found)
