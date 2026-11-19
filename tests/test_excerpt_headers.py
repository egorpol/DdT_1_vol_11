"""Check hand-written header excerpt wording against the manifest's crop record."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
M = 'http://www.music-encoding.org/ns/mei'
ID = '{http://www.w3.org/XML/1998/namespace}id'
STIMU_PREFIX = 'src.stimu1991.'
README_TARGET = '../supplemental_material/README.md'

NUMBER = re.compile(
    r'\d|\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|'
    r'thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|'
    r'forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|trillion)\b'
)


def excerpt_problems(text: str, bar: int, lst: int) -> list[str]:
    text = ' '.join(text.split()).casefold()
    excerpt_sentences = [
        sentence for sentence in re.split(r'(?<=\.)\s+', text)
        if re.search(r'\bexcerpts?\b', sentence)
    ]
    excerpt = ' '.join(excerpt_sentences)
    problems = []
    total = bar + lst
    if total == 0:
        if excerpt_sentences:
            problems.append('Remove the excerpt sentence when there are no crops.')
    else:
        if len(excerpt_sentences) > 1:
            problems.append('Keep the excerpt wording in one sentence.')
        singular, plural = 'A limited excerpt', 'Limited excerpts'
        required, forbidden = (singular, plural) if total == 1 else (plural, singular)
        if not re.search(rf'\b{required.casefold()}\b', excerpt):
            problems.append(f'Use "{required}".')
        if re.search(rf'\b{forbidden.casefold()}\b', excerpt):
            problems.append(f'Remove "{forbidden}".')

    bar_extent = r'\bone printed bar or less\b'
    if NUMBER.search(re.sub(bar_extent, ' ', excerpt)):
        problems.append('Remove the number from the excerpt sentence.')

    has_bar_extent = re.search(bar_extent, excerpt) is not None
    if bar and not has_bar_extent:
        problems.append('Include "one printed bar or less".')
    elif not bar and has_bar_extent:
        problems.append('Remove "one printed bar or less".')

    if lst:
        if not re.search(r"\ba single entry in the print['’]s list of misprints\b", excerpt):
            problems.append('Include "a single entry in the print’s list of misprints".')
    elif re.search(r'\blist of misprints\b', excerpt):
        problems.append('Remove "list of misprints".')
    return problems


def source_problems(source: ET.Element, bar: int, lst: int) -> list[str]:
    restrictions = source.findall(f'.//{{{M}}}useRestrict')
    text = ' '.join(''.join(restriction.itertext()) for restriction in restrictions)
    problems = excerpt_problems(text, bar, lst)
    if (bar or lst) and not any(
        ref.get('target') == README_TARGET
        for restriction in restrictions
        for ref in restriction.iter(f'{{{M}}}ref')
    ):
        problems.append(f'Add a ref targeting "{README_TARGET}" inside useRestrict.')
    return problems


def header_cases():
    manifest = ROOT / 'supplemental_material' / 'manifest.json'
    crop_counts = defaultdict(Counter)
    for item in json.loads(manifest.read_text(encoding='utf-8'))['items']:
        carrier = item['carrier_source']
        if carrier is None or not carrier.startswith(STIMU_PREFIX):
            continue
        kind = 'list' if '_errata_' in item['file'] else 'bar'
        crop_counts[item['mei_file'], carrier][kind] += 1

    matched = set()
    for path in sorted((ROOT / '11_buxtehude_sonatas_final').glob('*.mei')):
        mei_file = path.relative_to(ROOT).as_posix()
        for source in ET.parse(path).iter(f'{{{M}}}source'):
            source_id = source.get(ID, '')
            if source_id.startswith(STIMU_PREFIX):
                key = (mei_file, source_id)
                matched.add(key)
                counts = crop_counts[key]
                yield pytest.param(
                    mei_file, source_id, counts['bar'], counts['list'], source,
                    id=f'{path.stem}-{source_id}',
                )

    unmatched = sorted(crop_counts.keys() - matched)
    for index, (mei_file, source_id) in enumerate(unmatched, start=1):
        counts = crop_counts[mei_file, source_id]
        yield pytest.param(
            mei_file, source_id, counts['bar'], counts['list'], None,
            id=f'dangling-manifest-carrier-{index}',
        )


@pytest.mark.parametrize('mei_file, source_id, bar, lst, source', list(header_cases()))
def test_excerpt_header(mei_file, source_id, bar, lst, source):
    if source is None:
        problems = ['The manifest must point to an existing MEI file with this source ID.']
    else:
        problems = source_problems(source, bar, lst)
    if problems:
        detail = '\n'.join(f'- {problem}' for problem in problems)
        pytest.fail(
            f'{mei_file} ({source_id}), manifest crops (bar={bar}, list={lst})\n{detail}',
            pytrace=False,
        )


SINGULAR_TAIL = (
    'accompanies the critical annotation as a documentary image quotation; '
    'its attribution and intended reuse basis are recorded in the supplemental material.'
)
PLURAL_TAIL = (
    'accompany the critical annotations as documentary image quotations; '
    'their attribution and intended reuse basis are recorded in the supplemental material.'
)
BAR_SINGULAR = f'A limited excerpt of one printed bar or less {SINGULAR_TAIL}'
LIST_SINGULAR = f'A limited excerpt of a single entry in the print’s list of misprints {SINGULAR_TAIL}'
BAR_PLURAL = f'Limited excerpts, each of one printed bar or less, {PLURAL_TAIL}'
LIST_PLURAL = f'Limited excerpts, each of a single entry in the print’s list of misprints, {PLURAL_TAIL}'
MIXED_PLURAL = (
    'Limited excerpts, each of one printed bar or less or of a single entry '
    f'in the print’s list of misprints, {PLURAL_TAIL}'
)
NO_EXCERPT = 'Redistribution terms for the supplied library scans remain unconfirmed.'


@pytest.mark.parametrize(('bar', 'lst', 'text', 'expected'), [
    pytest.param(1, 0, BAR_SINGULAR, [], id='single-bar'),
    pytest.param(0, 1, LIST_SINGULAR, [], id='single-list'),
    pytest.param(2, 0, BAR_PLURAL, [], id='bar-plural'),
    pytest.param(7, 0, BAR_PLURAL, [], id='same-bar-wording-for-more-crops'),
    pytest.param(2, 1, MIXED_PLURAL, [], id='bar-and-list'),
    pytest.param(2, 4, MIXED_PLURAL, [], id='same-mixed-wording-for-more-crops'),
    pytest.param(0, 3, LIST_PLURAL, [], id='list-plural'),
    pytest.param(0, 0, NO_EXCERPT, [], id='no-crops'),
    pytest.param(
        1, 0, BAR_SINGULAR.upper().replace(' ', '\n  '), [], id='case-and-whitespace',
    ),
    pytest.param(
        1, 0, f'The facsimile reproduces 2 partbooks. {BAR_SINGULAR}',
        [], id='number-outside-excerpt-sentence',
    ),
    pytest.param(
        0, 1, LIST_SINGULAR.replace('print’s', "print's"), [], id='ascii-apostrophe',
    ),
    pytest.param(
        2, 0, f'Two limited measure-level excerpts {PLURAL_TAIL}',
        ['Use "Limited excerpts".', 'Remove the number from the excerpt sentence.',
         'Include "one printed bar or less".'],
        id='number-and-old-plural-extent',
    ),
    pytest.param(
        7, 0, f'Seven {BAR_PLURAL.lower()}',
        ['Remove the number from the excerpt sentence.'], id='number-word',
    ),
    pytest.param(
        2, 0, f'2 {BAR_PLURAL.upper()}',
        ['Remove the number from the excerpt sentence.'], id='digits',
    ),
    pytest.param(
        21, 0, f'Twenty-one {BAR_PLURAL.lower()}',
        ['Remove the number from the excerpt sentence.'], id='compound-number-word',
    ),
    pytest.param(
        7, 0, BAR_PLURAL.replace('Limited excerpts,', 'Limited excerpts, seven in all,', 1),
        ['Remove the number from the excerpt sentence.'], id='number-word-after-excerpt',
    ),
    pytest.param(
        7, 0, BAR_PLURAL.replace('Limited excerpts,', 'Limited excerpts (7),', 1),
        ['Remove the number from the excerpt sentence.'], id='digits-after-excerpt',
    ),
    pytest.param(
        2, 0, BAR_SINGULAR, ['Use "Limited excerpts".', 'Remove "A limited excerpt".'],
        id='singular-for-several',
    ),
    pytest.param(
        1, 0, BAR_PLURAL, ['Use "A limited excerpt".', 'Remove "Limited excerpts".'],
        id='plural-for-one',
    ),
    pytest.param(
        1, 0, f'A limited measure-level excerpt {SINGULAR_TAIL}',
        ['Use "A limited excerpt".', 'Include "one printed bar or less".'],
        id='old-singular-extent',
    ),
    pytest.param(
        2, 1, BAR_PLURAL, ['Include "a single entry in the print’s list of misprints".'],
        id='missing-list-kind',
    ),
    pytest.param(
        1, 1, f'The print’s list of misprints is not reproduced. {BAR_PLURAL}',
        ['Include "a single entry in the print’s list of misprints".'],
        id='list-kind-outside-excerpt-sentence',
    ),
    pytest.param(
        0, 1, LIST_SINGULAR.replace('a single entry in', 'a full page of', 1),
        ['Include "a single entry in the print’s list of misprints".'], id='full-page-of-list',
    ),
    pytest.param(
        3, 0, MIXED_PLURAL, ['Remove "list of misprints".'], id='extra-list-kind',
    ),
    pytest.param(
        0, 0, BAR_SINGULAR,
        ['Remove the excerpt sentence when there are no crops.', 'Remove "one printed bar or less".'],
        id='sentence-without-crops',
    ),
    pytest.param(
        0, 0, f'{NO_EXCERPT} A facsimile excerpt accompanies the critical annotation.',
        ['Remove the excerpt sentence when there are no crops.'],
        id='facsimile-excerpt-without-crops',
    ),
    pytest.param(
        2, 0, NO_EXCERPT, ['Use "Limited excerpts".', 'Include "one printed bar or less".'],
        id='sentence-missing',
    ),
    pytest.param(
        2, 0, f'{BAR_PLURAL} {BAR_PLURAL}', ['Keep the excerpt wording in one sentence.'],
        id='several-excerpt-sentences',
    ),
    pytest.param(
        1, 0, LIST_SINGULAR, ['Include "one printed bar or less".', 'Remove "list of misprints".'],
        id='wrong-kind',
    ),
])
def test_excerpt_problems(bar, lst, text, expected):
    assert excerpt_problems(text, bar, lst) == expected


@pytest.mark.parametrize(('target', 'expected'), [
    pytest.param('../supplemental_material/README.md', [], id='readme-ref'),
    pytest.param(
        '../supplemental_material/manifest.json',
        ['Add a ref targeting "../supplemental_material/README.md" inside useRestrict.'],
        id='wrong-ref-target',
    ),
])
def test_excerpt_ref_target(target, expected):
    sentence = BAR_SINGULAR.replace(
        'supplemental material', f'<ref target="{target}">supplemental material</ref>',
    )
    source = ET.fromstring(
        f'<source xmlns="{M}"><useRestrict>{NO_EXCERPT}</useRestrict>'
        f'<useRestrict>{sentence}</useRestrict></source>'
    )
    assert source_problems(source, 1, 0) == expected
