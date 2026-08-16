#!/usr/bin/env python3
"""Update the anonymous corpus progress grid in README.md.

The public README should not expose contributor names. This script reads the
page-oriented MEI files directly and classifies pages as:

- edited: the MEI header records work in mei-friend,
- not edited: an MEI file exists, but no mei-friend edit metadata is present,
- missing: a page number in the corpus sequence has no MEI file.

It writes ``docs/progress/page_grid.svg`` and replaces the generated block
between the progress markers in ``README.md``.
"""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


DEFAULT_CORPUS_DIR = (
    "11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199"
)
DEFAULT_README = "README.md"
DEFAULT_OUTPUT = "docs/progress/page_grid.svg"
START_MARKER = "<!-- progress-grid:start -->"
END_MARKER = "<!-- progress-grid:end -->"
PAGE_RE = re.compile(r"_(\d{5})_facs_zones\.mei$")


@dataclass(frozen=True)
class PageStatus:
    page: int
    state: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update README corpus progress grid."
    )
    parser.add_argument("--corpus-dir", default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--readme", default=DEFAULT_README)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--page-start",
        type=int,
        default=None,
        help="First page image number to show. Defaults to the first MEI file.",
    )
    parser.add_argument(
        "--page-end",
        type=int,
        default=None,
        help="Last page image number to show. Defaults to the last MEI file.",
    )
    parser.add_argument(
        "--timezone",
        default="Europe/Berlin",
        help="Timezone used for the README update date.",
    )
    return parser.parse_args()


def page_number(path: Path) -> int | None:
    match = PAGE_RE.search(path.name)
    return int(match.group(1)) if match else None


def is_mei_friend_edited(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    return "mei-friend" in text


def collect_statuses(
    corpus_dir: Path,
    page_start: int | None,
    page_end: int | None,
) -> list[PageStatus]:
    pages: dict[int, Path] = {}
    for path in corpus_dir.glob("*.mei"):
        number = page_number(path)
        if number is not None:
            pages[number] = path

    if not pages:
        raise SystemExit(f"No MEI page files found in {corpus_dir}")

    first = min(pages) if page_start is None else page_start
    last = max(pages) if page_end is None else page_end
    if first > last:
        raise SystemExit("--page-start must be smaller than --page-end")

    statuses: list[PageStatus] = []
    for page in range(first, last + 1):
        path = pages.get(page)
        if path is None:
            state = "missing"
        elif is_mei_friend_edited(path):
            state = "edited"
        else:
            state = "not_edited"
        statuses.append(PageStatus(page=page, state=state))
    return statuses


def counts(statuses: list[PageStatus]) -> dict[str, int]:
    return {
        "edited": sum(1 for status in statuses if status.state == "edited"),
        "not_edited": sum(1 for status in statuses if status.state == "not_edited"),
        "missing": sum(1 for status in statuses if status.state == "missing"),
    }


def render_svg(statuses: list[PageStatus], output_path: Path, updated: str) -> None:
    cols = 20
    cell = 24
    gap = 4
    margin_x = 28
    margin_top = 78
    margin_bottom = 72
    rows = (len(statuses) + cols - 1) // cols
    width = margin_x * 2 + cols * cell + (cols - 1) * gap
    height = margin_top + rows * cell + (rows - 1) * gap + margin_bottom
    palette = {
        "edited": "#2f7d59",
        "not_edited": "#d7dde5",
        "missing": "#f0a33a",
    }
    labels = {
        "edited": "edited in mei-friend",
        "not_edited": "not yet edited",
        "missing": "missing MEI file",
    }
    summary = counts(statuses)

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'role="img" aria-labelledby="title desc">',
        '<title id="title">Anonymous MEI page editing progress grid</title>',
        (
            '<desc id="desc">Grid of corpus page image numbers showing edited, '
            "not edited, and missing MEI pages.</desc>"
        ),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        (
            f'<text x="{margin_x}" y="30" font-family="Arial, sans-serif" '
            'font-size="18" font-weight="700" fill="#1f2933">'
            "Anonymous page editing status</text>"
        ),
        (
            f'<text x="{margin_x}" y="54" font-family="Arial, sans-serif" '
            'font-size="12" fill="#536170">'
            f'Updated {html.escape(updated)}; '
            f'{summary["edited"]} edited, '
            f'{summary["not_edited"]} not yet edited, '
            f'{summary["missing"]} missing</text>'
        ),
    ]

    for index, status in enumerate(statuses):
        col = index % cols
        row = index // cols
        x = margin_x + col * (cell + gap)
        y = margin_top + row * (cell + gap)
        label = labels[status.state]
        fill = palette[status.state]
        text_fill = "#ffffff" if status.state in {"edited", "missing"} else "#25313d"
        parts.extend([
            (
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
                f'fill="{fill}" stroke="#ffffff" stroke-width="1">'
                f"<title>Page {status.page:05d}: {html.escape(label)}</title>"
                "</rect>"
            ),
            (
                f'<text x="{x + cell / 2:.1f}" y="{y + 15}" '
                'text-anchor="middle" font-family="Arial, sans-serif" '
                f'font-size="7" font-weight="700" fill="{text_fill}">'
                f"{status.page}</text>"
            ),
        ])

    legend_y = height - 42
    legend_items = [
        ("edited", "edited in mei-friend"),
        ("not_edited", "not yet edited"),
        ("missing", "missing MEI file"),
    ]
    legend_x = margin_x
    for state, label in legend_items:
        parts.extend([
            (
                f'<rect x="{legend_x}" y="{legend_y}" width="14" height="14" '
                f'rx="3" fill="{palette[state]}"/>'
            ),
            (
                f'<text x="{legend_x + 20}" y="{legend_y + 11}" '
                'font-family="Arial, sans-serif" font-size="12" fill="#25313d">'
                f"{html.escape(label)}</text>"
            ),
        ])
        legend_x += 158

    parts.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def generated_markdown(
    statuses: list[PageStatus],
    output_path: Path,
    updated: str,
) -> str:
    summary = counts(statuses)
    total = len(statuses)
    existing = summary["edited"] + summary["not_edited"]
    return "\n".join([
        START_MARKER,
        f"![Anonymous page editing status]({output_path.as_posix()})",
        "",
        f"Updated: {updated}.",
        "",
        (
            f"Current anonymous page status: {summary['edited']} edited in "
            f"mei-friend, {summary['not_edited']} present but not yet edited, "
            f"and {summary['missing']} missing from the {total}-page image "
            f"sequence ({existing} MEI files currently present)."
        ),
        END_MARKER,
    ])


def update_readme(readme_path: Path, block: str) -> None:
    text = readme_path.read_text(encoding="utf-8")
    if START_MARKER not in text or END_MARKER not in text:
        raise SystemExit(
            f"README must contain {START_MARKER} and {END_MARKER} markers"
        )
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    readme_path.write_text(pattern.sub(block, text), encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = Path.cwd()
    corpus_dir = repo_root / args.corpus_dir
    readme_path = repo_root / args.readme
    output_path = Path(args.output)
    updated = datetime.now(ZoneInfo(args.timezone)).strftime("%Y-%m-%d")

    statuses = collect_statuses(corpus_dir, args.page_start, args.page_end)
    render_svg(statuses, repo_root / output_path, updated)
    update_readme(readme_path, generated_markdown(statuses, output_path, updated))


if __name__ == "__main__":
    main()
