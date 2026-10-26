# DdT validator and local CAMAT tools

The active tools are `scripts/validate_corpus.py`, `scripts/refresh_editorial_reports.py`,
`mei_corpus_checks.ipynb`,
`scripts/update_camat.py` and `scripts/sync_camat_viewer.py`. The validator imports
installed CAMAT's general engine, then applies this corpus's rules. It never
installs CAMAT, pulls Git, executes a notebook or rewrites MEI during checking.

## 1. Prepare or update CAMAT explicitly

From the corpus root, using the Python environment for validation and Jupyter:

```sh
python scripts/update_camat.py --dry-run
python scripts/update_camat.py
```

The default source is the neighboring local `camat_v2` checkout in the current
repository layout. Override it with `--checkout /path/to/camat_v2`. The helper
installs that checkout editable with `notebooks` and `validation` extras, runs
`pip check` and prints the actual installation/version/revision/source hashes.
Install libxml2's `xmllint` separately on `PATH`. Restart notebook kernels after
updating; a running kernel can retain old imports.

To obtain newer commits on the checkout's **current branch**:

```sh
python scripts/update_camat.py --pull
```

This requires a clean CAMAT worktree and uses `git pull --ff-only`, then installs
its dependencies. It does not switch branches, discard edits or create releases.
The committed reports need CAMAT 0.2.7 or newer: CAMAT 0.2.1–0.2.6 skip the
layer-duration checks in measures marked `metcon="false"`.

To install a remote Git snapshot instead of an editable checkout:

```sh
python scripts/update_camat.py --git-ref v0.2.7
```

A tag such as `v0.2.7` installs that release; a branch such as `main` installs
its current commit. This explicitly reinstalls the resolved Git code, even when
package metadata has not changed; it is not a continuous connection to the
remote branch. `--status` inspects the selected Python environment without
updating it. In an environment without pip, such as a uv venv, the helper runs
`uv pip` instead. It copies no validation code into this corpus.

A fresh clone can instead install the tested versions of every dependency,
CAMAT 0.2.7 from PyPI included, with `python -m pip install -r requirements.txt`.

Use the printed module/distribution versions, import path and commit rather than
inferring a package version from a branch or commit title.

## 2. Run general plus DdT checks

```sh
python scripts/validate_corpus.py --list-works
python scripts/validate_corpus.py --mode review --verovio --camat-parse
python -m jupyterlab mei_corpus_checks.ipynb
```

The notebook calls `plan_corpus_validation` and `run_corpus_validation` from the
same script; it has no second validator implementation. Review its configuration
and set `RUN_CHECKS=True` to execute. The CLI also supports repeatable `--work KEY`,
`--network`, `--no-ppq`, `--parsing-backend` and `--output-dir`. PPQ comparison
never strips attributes. `--skip-schematron` is diagnostic only and leaves
conformance incomplete.

`works.json` selects only the corrected first-sonata pilot for the publication workflow.
The separate `editorial-works.json` selects all assembled scores for shared editorial reports.
It is review-only and is rejected in release mode. Unreviewed work-specific staff roles
and source/catalogue identities are left explicit rather than copied from the pilot.

In the publication workflow, other MEI
files in its work directory are shown as **unlisted, not checked**. Add explicit
entries with each work's own identities, consulted sources, page range and staff
roles before expanding publication scope. Neither the pilot's five-staff map
nor its opus witness is applied automatically to appendix works or page OMR.
The manifest's unfinished editorial status and review/release fields are kept
unset until the actual review happens.

Three results are printed separately:

- **MEI conformance:** CAMAT's XML/references, selected official CMN 5.1 RELAX NG,
  real embedded Schematron, supplied offline resources and unchanged inputs.
- **Consumer diagnostics:** optional Verovio full rendering and CAMAT event-table
  probing. Musical review findings remain separate from schema validity.
- **DdT publication acceptance:** this corpus's header, license, source/work/file
  identity, responsibility, event-ID, staff-role, facsimile and annotation rules,
  plus release requirements in release mode.

The ten official pilot warnings about external IIIF canvas `surface/@corresp`
remain pending publication review. CAMAT retains their schema advisory severity;
DdT adds a publication reminder in review and blocks release. No waiver is
configured. Optional image networking tests HTTP image reachability/content type,
not bibliography, redistribution rights or musical correctness. A requested pass
with no HTTP targets is `not-applicable`, with a reason and request counts.

### Why the canvas warnings appear

The pilot uses `surface/@corresp` for a BSB IIIF canvas URL. RELAX NG accepts
its URI datatype. The embedded Schematron assertion instead tries to resolve
each value to an element's `xml:id` inside the MEI, as if it were a local
`#element-id` pointer. An external canvas URL does not match a local ID, so each
of the ten surfaces produces an advisory. See the [official linking attributes](https://music-encoding.org/guidelines/v5/attribute-classes/att.linking.html).

Image networking checks `graphic/@target`, the actual image endpoint. A passing
image request neither causes nor resolves the `corresp` warning. Keep the canvas
identity and the warning visible while publication treatment remains under
review. Ten schema advisories plus the DdT reminder make eleven report rows.

## 3. Read and retain the reports

The default CLI output is `validation/runs/latest`; the notebook uses
`validation/runs/notebook`. Both are replaceable, ignored run directories. The `_consistency_report.csv` files
beside the scores are tracked shared editorial reports. The notebook keeps its
optional single-work copy cell, which skips safely when no run was performed.
The full report set and its provenance are refreshed with the command below.
A small [committed pilot baseline](pilot-baseline.json) records the tested input,
schema, CAMAT state and result without machine-specific paths. It is a
validation snapshot, not a dependency pin or human publication sign-off. Use
`--output-dir validation/runs/2026-10-01-pilot` or a fresh notebook `REPORT_DIR`
when retaining evidence.

- Top-level `findings.csv` and `findings.json` contain the same combined rows
  from CAMAT and DdT. `origin` and `check` identify who produced each finding.
- Top-level `run.json` records shared pass execution, actual CAMAT identity,
  tool/schema/input hashes and DdT profile/work-list/rule/script hashes,
  selected works, corpus Git state and publication result.
- `general/findings.csv` and `general/findings.json` preserve CAMAT-only rows;
  these legitimately contain fewer findings when DdT adds its own rows.
- `general/run.json` preserves shared execution/progress. `general/schematron/`
  retains extracted rules, compiled validators and per-file SVRL.

Execution table rows are passes; CSV rows are individual findings; summary rows
are severity/category/check groups. A passing pass can still have advisory rows.
Disabled checks are `skipped`; missing/broken validators are `execution-error`.
Required skipped/inapplicable/unavailable checks cannot yield a pass. Interrupted
runs start incomplete and retain an active-pass marker. Native calls do not yet
have automatic hard timeouts. Source hashes verify bytes but cannot restore an
old dirty checkout; preserve its working sources and complete report folder.

### Refresh the reports used by contributors

```sh
python scripts/refresh_editorial_reports.py
```

This checks all 17 assembled MEI files against the installed CAMAT and current
DdT rules. It runs XML/reference, written-duration/PPQ, extra editorial diagnostics,
staff/term comparisons within each score, official RELAX NG and Schematron,
offline resource checks, full Verovio rendering and CAMAT event parsing.
HTTP image fetching is optional: add `--network`. Its skipped status is recorded.
Each score runs in its own worker process. If the native CAMAT consumer parser
crashes, its signal and failed attempt are retained; other checks are rerun in a
fresh process. That score explicitly records consumer diagnostics as incomplete
and CAMAT parsing as an execution error. The crash is included in its CSV.
No CAMAT update or MEI rewrite occurs. Op. II/1 joined this report set after
assembly on 2026-10-25; it remains `combined` pending work-level review.
Adding a new assembled file requires updating
`editorial-works.json`; an unlisted file makes refresh stop before overwriting reports.

CSV columns retain severity, category, check, file, source line, element/ID,
measure/staff/layer, message, expected/actual and context; `origin` distinguishes
CAMAT from DdT. Paths are repository-relative. Rows are sorted by severity and
source line. Additional DdT locations are filled from existing IDs where possible.
For musical editing, filter `category` (duration, ties, notation, terms, etc.).
Schema and DdT header/configuration warnings remain visible in the same file.
Existing blank headers now receive current metadata findings; a previously empty
report need not remain empty after the newer checks execute.

Regular duration findings include measures carrying `metcon="false"`. The marker
is retained in the finding's `context`; it no longer suppresses underfull or
overfull layer warnings. These remain review warnings because an anacrusis or a
subsidiary voice ending before the barline may be intentional. Read `expected`,
`actual`, the affected voice and the source together before editing. Hidden
`space` events contribute duration even though they draw no rest. Reports made
before the 2026-10-20 checker correction omitted these mismatches; use the actual
CAMAT source hash in report provenance to distinguish the runs. Validation does
not remove the marker or alter the musical text.

The 2026-10-20 source recheck covered all 16 assembled works. Of the 557 newly
visible duration findings, 479 were resolved by checking the DdT musical text and
repairing transcription, voice allocation or conversion padding. The remaining
78 warnings are intentional and stay in the regular CSVs: Appendix I has 62
voice-level findings in its twelve pickup/complementary ending measures (described
in its MEI editorial declaration); Op. II/2 has 16 nominal-meter findings for the
12/8 part against common-time accompaniment at measures 199–214 (documented in
two encoding annotations). The remaining 28 `metcon="false"` markers belong to
those passages. Full measures no longer carry inherited nonconformance markers.
These are reviewed working-edition results, not publication sign-off or a complete
pitch-by-pitch collation of the corpus.

`editorial-reports.json` is the committed provenance for the current report set:
CAMAT version/commit/source hash, dependency versions, schema/policy/code hashes,
per-score input and CSV hashes, execution statuses, result categories and finding
counts. After a selected-work refresh, that work's `validation_context` overrides
the shared CAMAT, dependency, schema, source and option fields. Other work entries
retain the shared context and their earlier results; a single-work refresh does
not imply that the entire report set was rerun with the newer CAMAT version.
Missing validators cannot be interpreted as a clean result. Exit code 1
means a selected score failed required checks or a requested consumer check;
its findings are still exported.
Review the summary alongside an empty CSV before treating it as clean.

CAMAT 0.2.5 crashed natively while parsing Appendix I and reported this as a
`camat_parse_native_crash` row: a tool execution failure, not a notation finding.
CAMAT 0.2.6 and later parse the score, and the committed reports record
`camat_parse` as passed for Appendix I. Should such a crash recur, base notation
changes on the musical/schema findings and source evidence, and use the batch
helper: a direct notebook consumer parse can terminate its kernel.

All validations finish before shared CSVs are replaced. An interrupted or raised
validation retains the previous report set. Previous CSVs and provenance are backed up
under ignored `validation/report-backups/`, and an export that fails partway
restores the files it replaced from that backup. Detailed new evidence is retained in
ignored `validation/runs/editorial/`. The notebook copy cell refreshes one CSV
only; rerun the batch command to refresh the complete provenance before committing.
Review the CSV/provenance diff and commit them with the relevant MEI changes.
The committed pilot baseline is historical; newer runs record the current code.

## 4. Inspect the score with the current CAMAT viewer

```sh
python scripts/sync_camat_viewer.py --dry-run
python scripts/sync_camat_viewer.py
python -m jupyterlab mei_facsimile_viewer.ipynb
```

The helper reads `notebooks/mei_facsimile_viewer.ipynb` from the local CAMAT
checkout (`--checkout` overrides it), retains the shared viewer cells, adapts
setup to the installed package and chooses the first manifest work as the
initial corpus-relative score. It does not install CAMAT or download tutorials.
The checkout-relative source path, commit, branch and notebook hash are recorded
in notebook metadata; the actual local path is printed during syncing. On later syncs it preserves recognized configuration assignments,
clears saved outputs and backs up the previous notebook under ignored
`validation/viewer-backups/`. New upstream options get their defaults; unrelated
custom cells are retained only in the backup. An unmanaged existing viewer is
not overwritten: archive or rename it first.

Syncing obtains the newest notebook saved in that checkout. Use the separate
update helper with `--pull` first when you want the latest remote code. Updating
the notebook and updating the installed package are distinct operations.

## Release mode and compatibility

```sh
python scripts/validate_corpus.py --mode release
python -m pytest tests -q
```

Release forces full Verovio rendering/CAMAT parsing and requires final file/URI,
release version/date, a locally available immutable commit whose MEI matches the
working files byte for byte, a local `v<version>` tag carrying the same MEI (the
versioned URI names the tag, since a file cannot contain its own commit), current
input hashes, persistent event IDs and hash-bound human sign-off. The initial supported
scope is `mei-data-only` and requires `CITATION.cff`. Sign-off must name an actual
reviewer and date and acknowledge the profile's review checks; annotation reviews
also confirm their reading/rationale/evidence. Automation does not fill them in.
Image redistribution inventories and complete archive/citation preparation still
require separate release work. Current topology checks cover primary surfaces,
page sequence/numbers, measure-zone/page links, unused or shared measure zones
and measure zones outside their surface; full system-band inference,
scan-derivative inventory and cross-work release coverage are not implemented.

A review exit code of zero means required general checks passed without hard
policy errors; `needs-review` is not publication acceptance. Release returns zero
only for an actual accepted result. Missing required passes and policy execution
errors return nonzero in both modes.

`scripts/check_mei_consistency.py` remains a small legacy CAMAT compatibility
wrapper with its old arguments. Use the dedicated script/notebook above for the
new read-only corpus workflow. Original local tools and saved outputs were
moved to ignored `docs/archive/local-tools/artifacts/`; see
[the migration audit](../docs/archive/local-tools/README.md). They are not imported
or executed by the new workflow.

## Responsibility boundary

CAMAT owns the general checks:

- XML readability, unique IDs and supported local or bundle pointer resolution
  in explicit standalone and assembly contexts, including `resp`, `source`, URI
  lists, document fragments and `xml:base`. Remote authority documents are not
  fetched.
- The unchanged official MEI 5.1 CMN RELAX NG and genuine execution of the
  embedded Schematron, with namespace preservation, XPath 2 rules, SVRL and
  handling of missing validators and incomplete runs. An XML schema
  declaration alone executes neither pass.
- Supplied offline raster and SVG resources and their declared coordinate
  bounds; optional HTTP image reachability. Facsimiles, IIIF and numeric
  surface names are not general MEI requirements.
- Musical diagnostics and the optional Verovio and CAMAT consumer probes, kept
  apart from schema validity. Alternative readings and complex timing still
  need contextual review; consumer tables do not prove event fidelity.
- Read-only orchestration, findings, execution and provenance records and
  input hashes. Conversion, assembly and cleanup are separate explicit calls.

This corpus owns its publication policy. `validation/profile.json`,
`validation/works.json` and `validation/rules.py` select the exact schema
declaration and hash, header paths and MEI-data license, work, file, catalogue
and source identity, the responsibility convention, persistent event IDs,
per-work staff roles, primary facsimile surfaces and page numbering,
measure-zone and page relationships, and annotation fields, evidence and
review. BuxWV numbers, the Uppsala opus witnesses and the pilot's five-staff
arrangement are local selections, not CAMAT defaults.

The page-level OMR files are in neither work list. Their
[README](../11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/README.md)
says which files are authoritative and lists known duplicate IDs and missing
zones.

For editorial requirements, see [the encoding profile](../docs/mei-encoding-profile.md)
and [editorial policy](../docs/editorial-policy.md). An automated report cannot
establish source-faithful pitch, rhythm, articulation, accidentals, figures or
readings.
