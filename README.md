# DdT 1, Vol. 11 — Dietrich Buxtehude: Instrumental Works

This repository contains a work-in-progress scholarly MEI edition of *Dietrich Buxtehudes Instrumentalwerke: Sonaten für Violine, Gambe und Cembalo*, edited by Carl Stiehl and published in 1903 as volume 11 of the first series of *Denkmäler deutscher Tonkunst*.

The edition is organized primarily as complete, sonata-level MEI files. It began with page-level optical music recognition (OMR) data from [musiconn.scoresearch](https://www.musiconn.de/services/musiconnscoresearch), which is being assembled and corrected against the [Bayerische Staatsbibliothek digital facsimile](https://digitale-sammlungen.de/en/view/bsb00023199). Editorial work is carried out with [mei-friend](https://mei-friend.mdw.ac.at/).

## Edition at a glance

|                     |                                                              |
| ------------------- | ------------------------------------------------------------ |
| Contents            | Fourteen sonatas in two opus groups and three appendix works |
| Encoding            | MEI 5.1, Common Music Notation customization                 |
| Editorial unit      | One MEI file per complete sonata or appendix work            |
| Facsimile alignment | IIIF-linked surfaces with measure-level zones                |
| Current state       | 16 of 17 works corrected, none finalized (0.9.0 pre-release) |

## Source edition

| Field                 | Description                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------------- |
| Composer              | Dietrich Buxtehude ([GND 118665685](https://d-nb.info/gnd/118665685))                        |
| Title                 | *Dietrich Buxtehudes Instrumentalwerke: Sonaten für Violine, Gambe und Cembalo*          |
| Series                | *Denkmäler deutscher Tonkunst*, first series, vol. 11                                    |
| Editor                | Carl Stiehl ([GND 117245674](https://d-nb.info/gnd/117245674))                               |
| Publication           | Leipzig: Breitkopf und Härtel, 1903                                                        |
| Extent                | 1 score (VIII, 185 pages)                                                                   |
| Holding institution   | Hochschule für Musik und Theater München, Bibliothek                                      |
| Shelfmark             | N2/X 1 DDT, 11                                                                              |
| BSB identifier        | `991009385569707356`                                                                      |
| BV number             | `BV035347306`                                                                             |
| WorldCat              | [OCLC 775063768](https://search.worldcat.org/oclc/775063768)                                 |
| Persistent identifier | [urn:nbn:de:bvb:12-bsb00023199-0](https://nbn-resolving.org/urn:nbn:de:bvb:12-bsb00023199-0) |
| Digital facsimile     | [Bayerische Staatsbibliothek](https://digitale-sammlungen.de/en/view/bsb00023199)            |

## Corpus contents

The status describes the complete work-level file, not the presence or edit history of its individual source pages.

| Work     | Key          | First printed page | First BSB image | MEI stem                                         | Status     |
| -------- | ------------ | -----------------: | --------------: | ------------------------------------------------ | ---------- |
| Op. I/1  | F major      |                  3 |           00013 | `op1_01_sonata_f_major`                        | corrected  |
| Op. I/2  | G major      |                 13 |           00023 | `op1_02_sonata_g_major`                        | corrected  |
| Op. I/3  | A minor      |                 22 |           00032 | `op1_03_sonata_a_minor`                        | corrected  |
| Op. I/4  | B-flat major |                 33 |           00043 | `op1_04_sonata_b_flat_major`                   | corrected  |
| Op. I/5  | C major      |                 44 |           00054 | `op1_05_sonata_c_major`                        | corrected  |
| Op. I/6  | D minor      |                 55 |           00065 | `op1_06_sonata_d_minor`                        | corrected  |
| Op. I/7  | E minor      |                 66 |           00076 | `op1_07_sonata_e_minor`                        | corrected  |
| Op. II/1 | B-flat major |                 79 |           00089 | `op2_01_sonata_b_flat_major`                   | pending    |
| Op. II/2 | D major      |                 90 |           00100 | `op2_02_sonata_d_major`                        | corrected  |
| Op. II/3 | G minor      |                103 |           00113 | `op2_03_sonata_g_minor`                        | corrected  |
| Op. II/4 | C minor      |                116 |           00126 | `op2_04_sonata_c_minor`                        | corrected  |
| Op. II/5 | A major      |                126 |           00136 | `op2_05_sonata_a_major`                        | corrected  |
| Op. II/6 | E major      |                139 |           00149 | `op2_06_sonata_e_major`                        | corrected  |
| Op. II/7 | F major      |                150 |           00160 | `op2_07_sonata_f_major`                        | corrected  |
| App. I   | —           |                160 |           00170 | `app_01_suite_to_op1_04`                       | corrected  |
| App. II  | C major      |                164 |           00174 | `app_02_sonata_2violins_gamba_cembalo_c_major` | corrected  |
| App. III | D major      |                176 |           00186 | `app_03_sonata_gamba_violin_cembalo_d_major`   | corrected  |

Status terms are used as follows:

- `pending`: no complete work-level MEI has been assembled.
- `combined`: source-page encodings have been assembled with linked facsimile surfaces.
- `corrected`: the musical text and facsimile references have been reviewed and local consistency checks completed.
- `finalized`: metadata, editorial review, validation, and publication naming are complete.

The 0.9.0 pre-release publishes the 16 assembled works as corrected, not finalized; the [finalization plan](docs/finalization-plan.md) lists what remains before 1.0. The work lists in [`validation/`](validation/README.md) record the same terms in `editorial_status`.

The App. III stem keeps its original `violin`; the printed score and the MEI work list name the violone (BuxWV 267).

## Repository contents

- [`11_buxtehude_sonatas_final/`](11_buxtehude_sonatas_final/) contains the primary combined sonata- and appendix-level editions. A temporary `_corr` filename suffix indicates a file still undergoing editorial work.
- [`11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/`](11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/) preserves the page-level OMR source material from which the work-level files were assembled.
- [`docs/mei-encoding-profile.md`](docs/mei-encoding-profile.md) documents the publication header, facsimile conventions, and validation profile.
- [`docs/editorial-workflow.md`](docs/editorial-workflow.md) records file naming, work-level statuses, and the correction sequence.
- [`validation/README.md`](validation/README.md) explains the checks, reports and release gate, and separates shared CAMAT checks from this edition's publication rules.
- [`docs/editorial-policy.md`](docs/editorial-policy.md) defines source relationships, correction categories and responsibility.
- [`docs/uppsala-facsimiles.md`](docs/uppsala-facsimiles.md) describes the private scan workflow and unresolved image terms.
- [`docs/finalization-plan.md`](docs/finalization-plan.md) lists what remains before the 1.0 release.
- [`CHANGELOG.md`](CHANGELOG.md) records the changes in each release; [`docs/release-notes/`](docs/release-notes/) holds each release's notes, validation record and known limitations.

Shared `_consistency_report.csv` files beside all assembled scores are tracked in Git for student editorial work. Refresh them together with `python scripts/refresh_editorial_reports.py`; [editorial report provenance](validation/editorial-reports.json) records the tested input/report hashes, actual CAMAT revision and executed checks. Full run artifacts and report backups stay local and ignored. The earlier [pilot validation baseline](validation/pilot-baseline.json) remains a historical snapshot; neither report set is publication sign-off.

## Check and inspect locally

Use Python 3.11 or newer and the same environment for these commands and the notebooks. With a neighboring CAMAT checkout:

```sh
python scripts/update_camat.py --dry-run
python scripts/update_camat.py
python scripts/validate_corpus.py --mode review --verovio --camat-parse
python scripts/refresh_editorial_reports.py
python scripts/sync_camat_viewer.py
```

For a standalone clone without a neighboring CAMAT checkout, use
`python scripts/update_camat.py --git-ref v0.2.7` to install CAMAT 0.2.7. Its
duration checks also cover measures marked `metcon="false"`, as the committed
reports do; CAMAT 0.2.1–0.2.6 skip them. This requires network access and
records the resolved code. Viewer syncing separately needs a local CAMAT
checkout, selected with `--checkout /path/to/camat_v2`; add `--ref v0.2.7` to
copy the released notebook rather than the checkout's working file.

Install libxml2's `xmllint` separately. Open
[`mei_corpus_checks.ipynb`](mei_corpus_checks.ipynb) for the same general + DdT
checks and [`mei_facsimile_viewer.ipynb`](mei_facsimile_viewer.ipynb) for source
inspection. Dependency updates and notebook syncing are explicit, separate
operations; validation records the actual CAMAT version/revision/source hashes.

The publication work list selects only Op. I/1. A separate review-only
[editorial work list](validation/editorial-works.json) covers all assembled scores
for shared reports; publication candidates still require explicit review. Its official IIIF Schematron warnings
remain pending publication review. See [the tool guide](validation/README.md)
for all options, reports, scope and release gates, and the
[migration audit](docs/archive/local-tools/README.md) for retired local tools.

Local TIFFs of the STIMU 1991 facsimile editions can be converted with
`python scripts/convert_uppsala_scans.py`. The [scan guide](docs/uppsala-facsimiles.md)
describes the `facsimiles/uppsala/op1` and `op2` layout, provenance and image
selection. These local images have not been cleared for public redistribution.

## Editorial approach

This is a corrected digital edition based on DdT 1903, retaining its staff layout and keyboard realization. Relevant historical witnesses are consulted through identified reproductions. OMR repairs, source-supported emendations, conjectural emendations and encoding notes are distinguished in the [editorial policy](docs/editorial-policy.md). Substantive departures from DdT are documented in the MEI. Each measure is linked to a zone on the corresponding facsimile surface, allowing the encoded notation and source image to be inspected together.

The MEI 5.1 CMN publication profile is applied to the pilot and is the target for finalizing the other work-level files. The work title, source description, responsibilities, editorial method, identifiers, revision history, and separate licensing of the MEI data and facsimile are recorded in the MEI header. Detailed implementation guidance is kept in the [MEI encoding profile](docs/mei-encoding-profile.md), rather than in this public overview.

## Contributors

Each MEI header records these responsibilities for its work in `titleStmt/respStmt`. MEI encoding and work-level assembly: CAMAT.

| Contributor           | OMR correction              | Editorial review           |
| --------------------- | --------------------------- | -------------------------- |
| Lea Meret Beck        | Op. I/4, II/3, App. II      | —                          |
| Ragna Conrads         | Op. I/5, II/4, App. III     | Op. I/5, II/4              |
| Francy Häring         | Op. I/1, I/2, I/7, II/6     | Op. I/1, I/2               |
| Jan-Raphael Kemnitzer | Op. I/2                     | Op. I/2                    |
| Egor Polyakov         | all 16 assembled works      | all 16, including metadata |
| Pia Steuck            | Op. I/5                     | —                          |
| Jingyu Tu             | Op. I/3, II/2, II/7, App. I | Op. I/3                    |
| You Zhou              | Op. I/6, II/5               | —                          |

## Funding

Work on this corpus is funded by the German Research Foundation (DFG), programme Library and Information Services — E-Research Technologies (LIS), grant PF 669/18-1.

## Citation

Until a versioned release is available, cite the repository with a commit or access date and cite the underlying source edition separately. The same metadata are in [`CITATION.cff`](CITATION.cff).

> Polyakov, Egor, Lea Meret Beck, Ragna Conrads, Francy Häring, Jan-Raphael Kemnitzer, Pia Steuck, Jingyu Tu, and You Zhou. *DdT 1, Vol. 11 — Dietrich Buxtehude: Instrumental Works*. Corrected MEI edition. CAMAT Corpus Editions. https://github.com/egorpol/DdT_1_vol_11.

> Dietrich Buxtehude. *Dietrich Buxtehudes Instrumentalwerke: Sonaten für Violine, Gambe und Cembalo*. Edited by Carl Stiehl. Leipzig: Breitkopf und Härtel, 1903. Digitized by the Bayerische Staatsbibliothek as `bsb00023199`.

## License

The MEI data and project-authored code/documentation are released under the [MIT License](LICENSE). The unchanged official MEI schema retains its upstream Educational Community License 2.0 notice.

Third-party facsimile images are separate from the MEI-data license. The [BSB source record](https://digitale-sammlungen.de/en/view/bsb00023199) offers its digitization of the 1903 print (copy held by the library of the Hochschule für Musik und Theater München) under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), as each MEI header records. The MEI files link to these images on the BSB IIIF server; this repository does not copy them. Reusing the images themselves, for example reproducing a page, falls under that license: credit the source, use them only non-commercially, and share adaptations under the same terms. The locally held STIMU/Uppsala scans and derivatives remain excluded from Git while their redistribution terms are unconfirmed; see the [scan guide](docs/uppsala-facsimiles.md).
