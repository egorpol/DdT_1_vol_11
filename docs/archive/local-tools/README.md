# Retired local tools — migration audit, 2026-10-01

The active workflow is [the corpus validator](../../../validation/README.md).
The files below were inspected before being removed from the active repository
root. Their exact original bytes and saved outputs remain in ignored `artifacts/`,
with `inventory.json` recording original paths and SHA-256 values. This is local
recovery material, not a runtime dependency or a public archive of contributor
progress data. The Excel assignment workbook stays in its original location.

## Editorial operations retained in CAMAT

- `fb_startid_to_tstamp_workflow.ipynb` demonstrates a dry run, optional Unicode
  normalization of ASCII figured-bass accidentals and application to a temporary
  copy. Its converter's function/class ASTs match `camat.convert_harm_startid_to_tstamp`;
  no unique conversion algorithm was found. A valid `harm/@startid` remains valid
  general MEI; conversion to `tstamp+staff` is an explicit editorial choice.
- `mei_corrected_full_checks.ipynb` has local `CLEAN_PPQ=True` and
  `CLEAN_ACCID_GES=True` in its inspected configuration, despite prose describing
  read-only defaults. Preserve this as historical intent, not a new validation
  default: performance timing and sounding accidentals can be meaningful.
  Single-layer normalization, accidental cleanup, conservative tie cleanup,
  figured-bass conversion, page-break linking and reports all have CAMAT helpers.
  The notebook contains orchestration/configuration, not an additional validator.
- Local `scripts/mei_consistency_workflow.py` has no unique top-level function/class
  names compared with CAMAT. CAMAT adds the newer URI/copy/assembly/schema behavior.
  `scripts/convert_harm_startid_to_tstamp.py` has identical converter declarations.
- The old `mei_facsimile_viewer.ipynb` and `scripts/mei_facsimile_viewer.py` preserve
  a pilot path, landscape/encoded layout and timed auto-watch configuration.
  No unique top-level viewer helper was found relative to CAMAT's viewer module.
  The active notebook is now a managed copy of CAMAT's current viewer; inspection
  options can be adjusted there, while all implementation stays in CAMAT.

The new validator never invokes these transformations. For a deliberate change,
use the CAMAT module's dry-run/apply route on selected copies and review the diff.

## Progress tracking retired separately

`mei_progress.py`, `mei_progress_plots.py` and
`progress_tracker_with_outputs_local.ipynb` read the local Excel assignments and
Git history and plot page-touch/commit/churn metrics. They contain no MEI editing
or validation transformations. These metrics do not prove source review or work
publication readiness and are not dependencies of the work-level validation.
Their original sources and saved outputs are kept locally together for recovery.
The earlier [public page-progress snapshot](../page-progress/README.md) is unchanged.

The [historical validation design](validation-design-2026-09-30.md) preserves the
original assessment, including future-tense statements that are no longer current.

## Additional local notes retained during push preparation

The former root `dokuwiki.txt` export and legacy `requirements.txt` are retained
byte-for-byte in ignored `artifacts/`, with a separate
`supplemental-cleanup-inventory.json`. They are local reference material; the
active environment uses CAMAT's `notebooks` and `validation` extras. The
[historical page variant](../encoding-variants/README.md) is preserved publicly
because it contains distinct encoding edits.
