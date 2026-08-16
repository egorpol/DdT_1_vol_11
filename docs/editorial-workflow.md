# Editorial Workflow

The principal editing unit is now the complete sonata or appendix work. Page-level MEI files are retained as source material, but progress and publication decisions are made at work level.

## Directory roles

- `11_buxtehude_sonatas_final/` contains the combined work-level MEI files and their temporary consistency reports.
- `11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/` contains the page-level OMR source files used during assembly.
- `docs/` contains editorial and technical documentation.
- Local notebooks and helper scripts support inspection and validation but are not edition content.

The former automatically generated page-progress grid is no longer an active measure of corpus progress. Its last snapshot and implementation are retained in [`archive/page-progress/`](archive/page-progress/) for provenance.

## Work-level sequence

1. Assemble the relevant page-level source files into one complete work when no combined file exists.
2. Correct the notation against the facsimile in mei-friend.
3. Confirm that surfaces, measure zones, page breaks, and system breaks represent the source structure.
4. Apply the [MEI encoding and publication profile](mei-encoding-profile.md).
5. Run schema, reference, facsimile-topology, musical-consistency, and Verovio checks.
6. Review the resulting report and compare the rendered score with the facsimile.
7. Confirm publication metadata and remove the temporary `_corr` suffix when the work is finalized.

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

`_corr` marks a working file. Final publication filenames omit that suffix. The same stem may be recorded in `meiHead/altId[@type='repository-stem']`.

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

The local facsimile viewer is intended for synchronized inspection of rendered notation and source images. The full-check notebook performs check-only validation by default and writes one `_consistency_report.csv` beside each selected work.

An empty report means only that the implemented automated checks found no inconsistency. It cannot determine whether every pitch, rhythm, articulation, accidental, figured-bass symbol, or editorial reading agrees with the printed source.

The pinned MEI 5.1 CMN schema at [`schemas/mei-CMN-5.1.rng`](../schemas/mei-CMN-5.1.rng) is used for reproducible and offline validation.
