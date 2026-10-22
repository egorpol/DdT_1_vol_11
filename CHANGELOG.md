# Changelog

All notable changes to this edition are recorded here. Version numbers follow the [encoding profile](docs/mei-encoding-profile.md#release-identity-versions-and-citation): patch releases for compatible corrections or metadata fixes that keep event IDs, minor releases for added works or coverage, and major releases for changes to event identity, segmentation or analytical interpretation. Musical corrections are listed even when the version step is small.

## [Unreleased]

### Added

- A web viewer in `site/`, ported from the Webern Op. 27 edition's: each work rendered by Verovio page by page beside its BSB facsimile page, measure zones linked both ways, links such as `#op2_02/189`, the editorial notes with their source excerpts, and two remembered display settings (mark every note target, box every measure). `scripts/build_site.py` assembles it and a GitHub Pages workflow publishes it.
- `scripts/check_site.py`, a headless check of the built or published viewer: every page of every work, with rendered measures against their zones, facsimile images, measure boxes and console errors. It needs Playwright, which `requirements.txt` leaves out.
- A one-measure facsimile excerpt for Op. I/1 m. 11, violin, from the STIMU 1991 reproduction of the Op. I print, in `supplemental_material/`: it shows the beaming that makes the C-sharp4 an eighth note (DdT prints a sixteenth). The annotation links it and the viewer shows it with the note, so all three source-supported emendations now have an excerpt.
- Three facsimile checks in the DdT validation rules (`validation/rules.py`), which CAMAT 0.2.7 runs only in its legacy publication profile: a measure zone that no measure references, a measure zone that more than one measure references, and a measure zone that extends beyond its surface. They report warnings in review mode and errors in release mode. All 16 works pass them.
- Release mode compares each selected MEI byte for byte with its copy at the manifest's `immutable_git_ref` and at the local release tag `v<release_version>`; before, it only checked that the commit existed.

### Changed

- A released MEI's `identifier[@type='versioned-URI']` names the release tag (`…/blob/v1.0.0/<file>`), not a commit: a file cannot contain the commit that contains it. The commit stays in the manifest.

### Fixed

- Op. II/1, BSB image `00099` (printed p. 89): restored page-local measure 18 by separating the final two bars, which were fused in imported measure 17. All existing musical event IDs and readings are preserved; the closing fermatas and arpeggio now belong to measure 18, linked to its previously unused facsimile zone, with the printed final barline. This page remains uncorrected OMR material.
- `mei_corpus_checks.ipynb`: the Git install example names the tested CAMAT release, `--git-ref v0.2.7`. It named the pre-release branch `beta/0.2.5`, which skips the duration checks in measures marked `metcon="false"` that the committed reports include.
- `scripts/refresh_editorial_reports.py`: an export that fails partway (a full disk, an interrupt) now restores every report it had replaced, and the provenance file, from the run's backup, so the CSVs and `validation/editorial-reports.json` stay in step. Before, the CSVs copied up to the failure stayed new while the provenance stayed old.
- Op. I/6, m. 126: the dynamics on staves 3 and 5 now read Forte, as DdT 1903 prints them (p. 62); they were encoded as Piano. The Piano in m. 125 is unchanged.
- App. III, m. 150: withdrew the conjectural dot on the keyboard lower-staff G2 and its annotation. DdT 1903 prints the dot (p. 182), so the encoded dotted half is the printed reading; the emendation rested on a misreading. The edition now has 21 editorial annotations: 3 source-supported emendations, 7 conjectural emendations and 11 encoding notes.
- Op. I/1, mm. 79–80: the encoding note on the A3 tie now says it crosses a system break, not a page break.
- Op. II/2, eleven measures corrected by Jingyu Tu. In m. 81 the third-beat continuo figure is one figure, 7♭, as DdT 1903 prints it (p. 92); it was encoded as a 7 stacked over a flat, which reads as a flat third. In m. 154 the closing 6 moves from the second eighth to the last sixteenth of beat 2, where the violin and the keyboard realization move. In m. 183 the gamba's second group of sixteenths has its stems down, as printed (p. 97). In mm. 89, 120, 166, 173–174, 181–182 and 189 the two layers of staff 5 (the lower staff of the keyboard realization) are numbered 1 and 2 instead of 5 and 6, so the upper one continues layer 1 of the single-layer measures; the other 15 two-layer measures of that staff (mm. 197–240) still number them 5 and 6. The consistency report is refreshed.
- The Op. II/6 m. 3 excerpt is re-cropped to 525 × 300 pixels: the old right edge cut through the head of the measure's last note, the E5 sixteenth.
- Web viewer: in the 17 measures with a blank figured-bass figure (`<f/>`, in Op. I/1, Op. II/6, Op. II/7 and App. II), the box drawn by "Measure boxes" and "Mark all notes" stretched to the top-left corner of the page (visibly in 16 of them), because Chrome counts the empty figure text as a point at the page origin. Empty texts are now left out before the boxes are measured.

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
