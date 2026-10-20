# Editorial Workflow

The principal editing unit is now the complete sonata or appendix work. Page-level MEI files are retained as source material, but progress and publication decisions are made at work level.

## Directory roles

- `11_buxtehude_sonatas_final/` contains the combined work-level MEI files. The accompanying consistency reports are tracked, shared editorial material for contributors; refresh all reports with `python scripts/refresh_editorial_reports.py`.
- `11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/` contains the page-level OMR source files used during assembly.
- `docs/` contains editorial and technical documentation.
- `mei_corpus_checks.ipynb` is the thin interface to the corpus validator; `mei_facsimile_viewer.ipynb` is a synchronized CAMAT inspection notebook. Retired local tools are preserved in an ignored recovery archive, outside the active workflow.

The former automatically generated page-progress grid is no longer an active measure of corpus progress. Its last snapshot and implementation are retained in [`archive/page-progress/`](archive/page-progress/) for provenance.

## Work-level sequence

1. Assemble the relevant page-level source files into one complete work when no combined file exists.
2. Correct the notation against the DdT facsimile in mei-friend, consulting the relevant Uppsala print where needed. Follow the [editorial policy](editorial-policy.md) and record substantive departures from DdT at the affected events.
3. Confirm that surfaces, measure zones, page breaks, and system breaks represent the source structure.
4. Apply the [MEI encoding and publication profile](mei-encoding-profile.md).
5. Run schema, reference, facsimile-topology, musical-consistency, and Verovio checks, recording which checks actually ran. See [validation-workflow.md](validation-workflow.md) for implemented checks and the remaining scope limits.
6. Review the resulting report and compare the rendered score with the facsimile.
7. Review the editorial annotations, confirm release metadata, remove the temporary `_corr` suffix, and update the publication URI and corpus manifest together. Follow the release-identity rules in the [publication profile](mei-encoding-profile.md).

Cleanup or rewrite options in validation tooling should remain disabled by default. Enable them only for a deliberate, reviewed transformation of selected files.

## File naming

Sonata-level working files use sortable stems:

```text
buxtehude_op<opus-number>_<work-number>_sonata_<key>_corr.mei
```

Appendix works use:

```text
buxtehude_app_<work-number>_<short-title>_<key>_corr.mei
```

`_corr` marks a working file. Final publication filenames omit that suffix. `meiHead/altId[@type='repository-stem']` preserves the shorter local edition key without `buxtehude_` or `_corr`, for example `op1_01_sonata_f_major`. Thus the final filename is `buxtehude_<local-key>.mei`. This is an explicit mapping, not a requirement that `altId` match the literal current filename.

Page-level source filenames retain the BSB image identifier:

```text
bsb00023199_<image-number>_facs_zones.mei
```

In this digitization, printed score pages and BSB image numbers are offset by ten: printed page 3 corresponds to image `00013`, for example. Work-level surface numbering is independent and begins with `1`.

## Status vocabulary

- `pending`: no complete work-level MEI has been assembled.
- `combined`: source-page encodings have been assembled with linked facsimile surfaces.
- `corrected`: the musical text and facsimile references have been reviewed and local consistency checks completed.
- `finalized`: metadata, editorial review, validation, and publication naming are complete.

Update the work table in the main README when the work-level status changes. Page-by-page edit metadata is not used for the public status.

## Local inspection and validation

Prepare/update the installed CAMAT package with `python scripts/update_camat.py`.
Run `python scripts/validate_corpus.py --mode review --verovio --camat-parse`, or
open `mei_corpus_checks.ipynb` and enable `RUN_CHECKS` after reviewing its plan.
The same functions run general CAMAT validation plus explicit DdT rules; no
cleanup or dependency update occurs during checking.

Refresh the viewer with `python scripts/sync_camat_viewer.py`, then open
`mei_facsimile_viewer.ipynb` for synchronized notation/source inspection. Its
implementation lives in installed CAMAT. See [the tool guide](../validation/README.md)
for source updates, paths, report meanings and review/release commands, and
[validation responsibilities](validation-workflow.md) for the rule boundary.

An empty report means only that the implemented automated checks found no inconsistency. It cannot determine whether every pitch, rhythm, articulation, accidental, figured-bass symbol, or editorial reading agrees with the printed source.

The pinned MEI 5.1 CMN schema at [`schemas/mei-CMN-5.1.rng`](../schemas/mei-CMN-5.1.rng) is used for reproducible and offline validation.
