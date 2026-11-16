# Work reviews with Verovio renderings: record of 2026-10-18 to 2026-10-20

From 2026-10-18 to 2026-10-20, an AI coding agent (OpenAI Codex) reviewed
work-level reports and Verovio renderings with the editor. This is work from
the [edition workflow](editorial-workflow.md)'s steps 3 and 6; a paper on the
CAMAT toolkit, in preparation, calls it step 4. The edition's own fourth step
applies the encoding profile. The agent
ran checks, inspected renderings and made repairs; the editor guided the review.
This page and the folder
[`render-review-2026-10-18/`](render-review-2026-10-18/) are the durable record.
They were reconstructed in November 2026 from git-ignored run folders and the
agent's session log, not written at the time. Neither the run folders nor the
log is tracked in the repository. All times below are UTC (`Z`).

## Versions

- App: Codex Desktop 0.163.0-alpha.10.2, one session; model `gpt-6.1-sol`
  in all 57 turns, reasoning effort `xhigh`.
- Tools: Verovio 6.3.0 (`6.3.0-425dd7b`), CAMAT 0.2.6 (a local checkout), lxml, Pillow and
  `rsvg-convert` for SVG-to-PNG conversion.

## Complete-work commits

Of the session's 15 "Complete …" commits, 12 subjects say "review". The others
say "sources and editorial annotations" (I/1), "metadata and encoding checks"
(I/4), and "source corrections and encoding checks" (I/5).

| Work | Commit | UTC time |
|---|---|---|
| Op. I/1 | [`2a2a007f`](https://github.com/egorpol/DdT_1_vol_11/commit/2a2a007ffc734b8a30280752ce967405729fac19) | 2026-10-18T23:03:06Z |
| Op. I/3 | [`0f7d89fa`](https://github.com/egorpol/DdT_1_vol_11/commit/0f7d89fa106e93a9f8831188a948a23b39a6415e) | 2026-10-19T00:12:32Z |
| Op. I/4 | [`5728de6b`](https://github.com/egorpol/DdT_1_vol_11/commit/5728de6b652d94932196be753462cc05bf63e581) | 2026-10-19T00:18:36Z |
| Op. I/5 | [`ae304072`](https://github.com/egorpol/DdT_1_vol_11/commit/ae304072374865617023befae8173d822cb8d674) | 2026-10-19T00:43:50Z |
| Op. I/6 | [`b6f298c9`](https://github.com/egorpol/DdT_1_vol_11/commit/b6f298c96c0a797163c9294aac28d6d986f94f6a) | 2026-10-19T01:15:04Z |
| Op. I/7 | [`4cfb232f`](https://github.com/egorpol/DdT_1_vol_11/commit/4cfb232f24f313c229339fbca668079600517661) | 2026-10-19T09:35:51Z |
| Op. II/2 | [`7f4ac0ce`](https://github.com/egorpol/DdT_1_vol_11/commit/7f4ac0ceeec5c10b618b55c93cc3497abfc7cbb2) | 2026-10-19T21:10:34Z |
| Op. II/3 | [`f59304c2`](https://github.com/egorpol/DdT_1_vol_11/commit/f59304c2d8c1176ed1b3b6ab2a8d3552cf8fba7b) | 2026-10-19T22:06:09Z |
| Op. II/4 | [`79b088f5`](https://github.com/egorpol/DdT_1_vol_11/commit/79b088f59c2b2c87d2dcac436190815165947a09) | 2026-10-20T01:57:12Z |
| Op. II/5 | [`da994ac3`](https://github.com/egorpol/DdT_1_vol_11/commit/da994ac30c75ad9ed3d3a9ddf50b5a930278d04e) | 2026-10-20T02:26:56Z |
| Op. II/6 | [`57464bad`](https://github.com/egorpol/DdT_1_vol_11/commit/57464bad16990551e33c17ed9650a6b31d4e20fd) | 2026-10-20T02:51:47Z |
| Op. II/7 | [`665232c9`](https://github.com/egorpol/DdT_1_vol_11/commit/665232c9901a2becd97d5194fc48dede4573b8d9) | 2026-10-20T03:11:58Z |
| App. I | [`3517d0d4`](https://github.com/egorpol/DdT_1_vol_11/commit/3517d0d448beb92f1654d5766355adc85bebf3c4) | 2026-10-20T07:27:52Z |
| App. II | [`75165a61`](https://github.com/egorpol/DdT_1_vol_11/commit/75165a6149c1a308672a05bbebf97295c2b190dc) | 2026-10-20T12:00:20Z |
| App. III | [`8185731d`](https://github.com/egorpol/DdT_1_vol_11/commit/8185731d178a0c2140a940d7898933ba782b01ec) | 2026-10-20T12:36:37Z |

## The print check

The II/5 audit derives expected page and system starts from facsimile zones,
not `pb`/`sb`. A bar on a new `surface` starts a page. On the same surface, a
zone whose `ulx` is more than 100 px left of the prior zone's starts a system.
The saved audit scripts of II/6, II/7 and App. I–III use the same rule. The
session commands for I/7 and II/2–II/4 also took the starts from the zones, by
other rules (for I/7 and II/3–II/4, from the zones' vertical positions).

The render script uses Verovio with `breaks: encoded`. For each page and system
it reads the bars from the SVG's `measure`-class ids and asserts the system
starts against the zone-derived starts. It asserts 13 pages and bars 1–207
each once, and renders 8 flagged bar ranges alone. It saves SVGs, PNGs and 13
combined page images, with the DdT scan left and the rendering right.

The finish script exports the CAMAT CSV and asserts 14 warnings and 2 infos.
It reverses documented edits and compares canonical XML with the backup to
account for the music diff. It asserts no rhythm or tie issues, staff totals
matching the meter and a layout hash matching the score. It checks the Git index,
HEAD, unrelated files and other work records are unchanged, then saves evidence.

`layout-audit.json` records 13 pages, 51 systems and 207 bars, with
`all_source_boundaries_match` and `all_measures_once` both true; the render
script writes the file only after those assertions pass. Its
`score_sha256` begins `2e5b518b` and equals the II/5 MEI at `da994ac3`;
the parent commit's file differs. The rendered layout matches the zones' layout.

In its II/5 `review-notes.md`, the agent wrote, in its own words:

> All thirteen page comparisons were visually inspected for source boundaries
> and the identified notation issues.

> This targeted consistency/source review is not a claim of full note-by-note
> collation of every printed event.

II/2 had 31 encoded pages and 54 systems against the print's 13 and 51. Its
repair plan moved 8 breaks, removed 3, changed 17 page breaks to system breaks
and 2 the reverse; the categories overlap. In II/5, 8 false page breaks became
system breaks.

## Scope per work

The print check ran for 10 works, listed below. Saved scripts hold it for 6
(II/5–II/7, App. I–III). For I/7 and II/2–II/4 it ran as session commands;
outputs remain in the run folders. For all 10, the run folders hold images
that put DdT pages beside their renderings.

| Work | Print-check form | Pages | Systems | Bars |
|---|---|---:|---:|---:|
| Op. I/7 | Session commands | 11 | 43 | 251 |
| Op. II/2 | Session commands | 13 | 51 | 281 |
| Op. II/3 | Session commands | 13 | 51 | 232 |
| Op. II/4 | Session commands | 10 | 39 | 227 |
| Op. II/5 | Saved scripts | 13 | 51 | 207 |
| Op. II/6 | Saved scripts | 11 | 43 | 195 |
| Op. II/7 | Saved scripts | 10 | 39 | 217 |
| App. I | Saved scripts | 4 | 15 | 89 |
| App. II | Saved scripts | 12 | 36 | 186 |
| App. III | Saved scripts | 10 | 39 | 226 |

The earlier Op. I/3–I/6 reviews saved single-bar before/after renderings only;
the Op. I/1 review saved no renderings. None of the five compared a rendered page
with the print; for I/6 the agent marked system starts on DdT scans, without a
rendering. Op. I/2 and II/1 were reviewed outside the session.

The recheck of the `metcon` markers (MEI's flag for a bar whose length departs
from the meter) on 2026-10-20, from 16:04Z, rendered 13 works (I/1–I/7,
II/2–II/7) page by page and selected bars alone. It asserted system starts
against the MEI's own `pb`/`sb`, not the zones, and each bar once. It paired no
rendering with a scan. Its outputs are in
`validation/runs/metcon-regular-reports-20261020T160454008474Z/`.

For each work, the editor requested fresh reports and checks, answered questions
on witnesses and decided proposed conjectural emendations. The editor approved
each commit and push, requested I/7's page/system-break check and started the
metcon recheck. After the agent's App. II pass, the editor found the gamba clef
error from m. 32, the m. 34 chord error and the m. 70 dot error.

## Files in `render-review-2026-10-18/`

| File | Content |
|---|---|
| `ddt-op2-05-audit.py` | Zone-derived starts, duration and tie checks. |
| `ddt-op2-05-render.py` | Page/system assertions, page pairs and isolated bar ranges. |
| `ddt-op2-05-finish.py` | Report export, music-diff and preservation checks. |
| `layout-audit.json` | II/5's rendered layout and score hash. |

These four files are unedited, byte-for-byte copies documenting what ran in
`validation/runs/op2-05-final-review-20261020T021247200379Z/`. Scripts do not
run outside the editor's machine and session. Seven lines hard-code its root
or use `/tmp` files written earlier in the session:

- `ddt-op2-05-audit.py:7`, `ddt-op2-05-render.py:6` and
  `ddt-op2-05-finish.py:9`: each hard-codes the editor's local repository root.
- `ddt-op2-05-audit.py:9` and `ddt-op2-05-render.py:7`: each reads
  `/tmp/ddt-op2-05-fresh-review`, a pointer file holding the fresh run-folder path.
- `ddt-op2-05-finish.py:11`: reads `/tmp/ddt-op2-05-final-review`,
  `/tmp/ddt-op2-05-fresh-review` and `/tmp/ddt-op2-05-review-backup`, pointer
  files holding the final, fresh and backup run-folder paths.
- `ddt-op2-05-finish.py:81`: names the earlier session copies
  `/tmp/ddt-op2-05-audit.py` and `/tmp/ddt-op2-05-render.py` for copying to the run.

Not included:

- The scans, crops, renderings and combined page images.
- The other runs' scripts and outputs, the session log and `review-notes.md`.

## Limits

- The print check establishes layout agreement with the encoded zones. It does
  not establish the correctness of each printed event's transcription.
- The visual-inspection statement above is the agent's own account in its II/5
  notes. In App. II, the editor found three errors after the agent's pass (above).
