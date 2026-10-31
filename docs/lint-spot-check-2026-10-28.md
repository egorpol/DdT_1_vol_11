# Editor's lint spot-check: review of 2026-10-28

On 2026-10-28 the editor checked the 12 passages corrected in the second
musical-lint triage pass (CHANGELOG, Unreleased, "Fixed") before approving the
fixes. Each card of a local review page showed the DdT 1903 page crop beside
renderings of v0.10.0 and of the corrected encoding, with ok / problem marks.
This file records the verdicts. It is the editor's spot-check of passages that
had already been corrected, not a collation of the edition or an independent
review.

## The page

- Builder `validation/runs/lint-open-items/tools/build_review.py` (one-off,
  DdT-specific); page `validation/runs/lint-open-items/review/index.html`
  ("Lint spot-check", 12 cards). Both are git-ignored (`validation/.gitignore`:
  `runs/`) and exist only locally.
- The page keeps its marks in the browser. The editor copied its summary into
  the editing session at 12:52 UTC; the table below reproduces it.

## Verdicts

| Card | Verdict | Outcome |
|---|---|---|
| Op. II/3, m. 229 | ok | |
| Op. II/3, m. 227 | ok | |
| Op. II/3, m. 228 | ok | |
| Op. II/3, m. 230 | ok | |
| Op. II/3, m. 231 | ok | |
| Op. II/3, m. 232 | ok | |
| Op. II/3, m. 112 | ok | |
| Op. I/2, m. 36 | ok | |
| Op. I/6, mm. 13–14 | problem: the two added keyboard ties curved the wrong way ("b4 => lower, d5 => upper") | Fixed before the commit: the B4 tie curves below, the D5 tie above |
| App. I, m. 82 | ok | |
| Op. II/3, mm. 41–44 | ok; note: "we need to integrate both uppsala crops into viewer" | Open; no other DdT file records the request (2026-10-31) |
| Op. I/5, mm. 112–168: figures (57 rows) | ok ("all looks ok"); 1 of 57 rows marked (m. 112 ok) | |

12 cards: 11 ok, 1 problem.

## After the review

- The fixes, with the Op. I/6 tie directions corrected, are in commit
  [`92384f5b`](https://github.com/egorpol/DdT_1_vol_11/commit/92384f5b5d357d088a1b272d54f87d2f16156c64)
  ("Close the open lint items of the 0.10.0 notes", 2026-10-28), after the
  v0.10.0 tag.
- In the same session the editor removed the segno over the violin in Op. II/3
  m. 229 (`csop3re`), which DdT does not print.
- The page's design became CAMAT's generic review page (`camat-review-page`,
  CAMAT PR #24).

## Limits

- The reviewer was the editor, and every passage had already been corrected.
  A mark records that the editor looked at the passage against the page image;
  it is not a collation and not inter-annotator agreement.
- The page and its browser marks are local. This file is the durable record.
