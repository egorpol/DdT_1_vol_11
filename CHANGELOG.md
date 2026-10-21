# Changelog

All notable changes to this edition are recorded here. Version numbers follow the [encoding profile](docs/mei-encoding-profile.md#release-identity-versions-and-citation): patch releases for compatible corrections or metadata fixes that keep event IDs, minor releases for added works or coverage, and major releases for changes to event identity, segmentation or analytical interpretation. Musical corrections are listed even when the version step is small.

## [Unreleased]

### Added

- A web viewer in `site/`, ported from the Webern Op. 27 edition's: each work rendered by Verovio page by page beside its BSB facsimile page, measure zones linked both ways, links such as `#op2_02/189`, the editorial notes with their source excerpts, and two remembered display settings (mark every note target, box every measure). `scripts/build_site.py` assembles it and a GitHub Pages workflow publishes it.
- A one-measure facsimile excerpt for Op. I/1 m. 11, violin, from the STIMU 1991 reproduction of the Op. I print, in `supplemental_material/`: it shows the beaming that makes the C-sharp4 an eighth note (DdT prints a sixteenth). The annotation links it and the viewer shows it with the note, so all three source-supported emendations now have an excerpt.

## [0.9.0] — 2026-10-21

First public pre-release. The 16 assembled works are **corrected, not finalized**: their musical text and facsimile links have been reviewed against DdT 1903 and their consistency reports completed, but publication sign-off, final filenames and the release-mode gate are still open. See the [release notes](docs/release-notes/0.9.0.md) for the validation record and known limitations, and the [1.0 checklist](docs/finalization-plan.md) for what remains.

### Added

- Work-level MEI 5.1 CMN files for 16 of the 17 works in DdT 1, vol. 11: Op. I/1–7, Op. II/2–7 and Appendix I–III (3,276 measures). Each measure points to a zone on one of 170 surfaces linked to the Bayerische Staatsbibliothek IIIF facsimile. Op. II/1 is not yet assembled.
- Header metadata per work: title, composer, responsibilities, DdT 1903 source description with BSB identifiers and printed page range, consulted Uppsala witnesses where used, editorial declaration, BuxWV number, revision history and the MIT licence for the MEI data. Every header reads `<edition n="0.9.0">Corrected working edition (pre-release)</edition>`.
- 22 editorial annotations at the affected events: 3 source-supported emendations, 8 conjectural emendations and 11 encoding notes, plus 2 encoding notes on the notated meter in Op. II/2.
- Two one-measure facsimile excerpts from the STIMU 1991 reproduction of the Op. II print (Op. II/2 m. 189, Op. II/6 m. 3) in `supplemental_material/`, with their own attribution and rights note. The MIT licence does not cover them.
- A tracked consistency report beside each score (`*_consistency_report.csv`) and its provenance in `validation/editorial-reports.json`.
- Corpus validation: `scripts/validate_corpus.py` (CAMAT's general MEI checks plus this edition's publication rules in `validation/rules.py` and `validation/profile.json`), `scripts/refresh_editorial_reports.py`, helpers for installing CAMAT and syncing its viewer notebook, the `mei_corpus_checks.ipynb` and `mei_facsimile_viewer.ipynb` notebooks, a test suite in `tests/`, and the tested dependency versions in `requirements.txt`.
- Documentation: [editorial policy](docs/editorial-policy.md), [encoding profile](docs/mei-encoding-profile.md), [editorial workflow](docs/editorial-workflow.md), [encoding and rendering issues](docs/issues.md), [Uppsala scan guide](docs/uppsala-facsimiles.md), [1.0 checklist](docs/finalization-plan.md) and [`CITATION.cff`](CITATION.cff).

### Kept from earlier work

- The page-level OMR files from musiconn.scoresearch in `11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/`, from which the work-level files were assembled. They are source material, not part of the edition text.

[0.9.0]: https://github.com/egorpol/DdT_1_vol_11/releases/tag/v0.9.0
