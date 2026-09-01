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
| Current state       | Active correction, metadata review, and validation           |

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

| Work     | Key          | First printed page | First BSB image | MEI stem                                         | Status    |
| -------- | ------------ | -----------------: | --------------: | ------------------------------------------------ | --------- |
| Op. I/1  | F major      |                  3 |           00013 | `op1_01_sonata_f_major`                        | corrected |
| Op. I/2  | G major      |                 13 |           00023 | `op1_02_sonata_g_major`                        | combined  |
| Op. I/3  | A minor      |                 22 |           00032 | `op1_03_sonata_a_minor`                        | corrected |
| Op. I/4  | B-flat major |                 33 |           00043 | `op1_04_sonata_b_flat_major`                   | corrected |
| Op. I/5  | C major      |                 44 |           00054 | `op1_05_sonata_c_major`                        | corrected |
| Op. I/6  | D minor      |                 55 |           00065 | `op1_06_sonata_d_minor`                        | corrected |
| Op. I/7  | E minor      |                 66 |           00076 | `op1_07_sonata_e_minor`                        | corrected |
| Op. II/1 | B-flat major |                 79 |           00089 | `op2_01_sonata_b_flat_major`                   | pending   |
| Op. II/2 | D major      |                 90 |           00100 | `op2_02_sonata_d_major`                        | corrected |
| Op. II/3 | G minor      |                103 |           00113 | `op2_03_sonata_g_minor`                        | combined  |
| Op. II/4 | C minor      |                116 |           00126 | `op2_04_sonata_c_minor`                        | combined  |
| Op. II/5 | A major      |                126 |           00136 | `op2_05_sonata_a_major`                        | combined  |
| Op. II/6 | E major      |                139 |           00149 | `op2_06_sonata_e_major`                        | corrected |
| Op. II/7 | F major      |                150 |           00160 | `op2_07_sonata_f_major`                        | pending   |
| App. I   | —           |                160 |           00170 | `app_01_suite_to_op1_04`                       | combined  |
| App. II  | C major      |                164 |           00174 | `app_02_sonata_2violins_gamba_cembalo_c_major` | combined  |
| App. III | D major      |                176 |           00186 | `app_03_sonata_gamba_violin_cembalo_d_major`   | combined  |

Status terms are used as follows:

- `pending`: no complete work-level MEI has been assembled.
- `combined`: source-page encodings have been assembled with linked facsimile surfaces.
- `corrected`: the musical text and facsimile references have been reviewed and local consistency checks completed.
- `finalized`: metadata, editorial review, validation, and publication naming are complete.

## Repository contents

- [`11_buxtehude_sonatas_final/`](11_buxtehude_sonatas_final/) contains the primary combined sonata- and appendix-level editions. A temporary `_corr` filename suffix indicates a file still undergoing editorial work.
- [`11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/`](11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/) preserves the page-level OMR source material from which the work-level files were assembled.
- [`docs/mei-encoding-profile.md`](docs/mei-encoding-profile.md) documents the publication header, facsimile conventions, and validation profile.
- [`docs/editorial-workflow.md`](docs/editorial-workflow.md) records file naming, work-level statuses, and the correction and validation workflow.

CSV files ending in `_consistency_report.csv` are working reports produced during correction. An empty report means that the automated checks found no encoded inconsistency; it does not replace comparison with the source facsimile.

## Editorial approach

The encoding is intended to reproduce the notation of the printed source while correcting OMR and conversion errors. Explicit editorial interventions are recorded in the MEI rather than silently presented as source readings. Each measure is linked to a zone on the corresponding facsimile surface, allowing the encoded notation and source image to be inspected together.

Every complete work uses a consistent MEI 5.1 CMN publication profile. The work title, source description, responsibilities, editorial method, identifiers, revision history, and separate licensing of the MEI data and facsimile are recorded in the MEI header. Detailed implementation guidance is kept in the [MEI encoding profile](docs/mei-encoding-profile.md), rather than in this public overview.

## Funding

Work on this corpus is funded by the German Research Foundation (DFG), programme Library and Information Services — E-Research Technologies (LIS), grant PF 669/18-1.

## Citation

Until a versioned release and its preferred citation are available, cite the repository with a commit or access date and cite the underlying source edition separately:

> CAMAT Corpus Editions. *DdT 1, Vol. 11 — Dietrich Buxtehude: Instrumental Works*. Work-in-progress MEI corpus.

> Dietrich Buxtehude. *Dietrich Buxtehudes Instrumentalwerke: Sonaten für Violine, Gambe und Cembalo*. Edited by Carl Stiehl. Leipzig: Breitkopf und Härtel, 1903. Digitized by the Bayerische Staatsbibliothek as `bsb00023199`.

## License

The MEI data and repository materials are released under the [MIT License](LICENSE).

The historical source is in the public domain. Reuse of facsimile images and metadata remains subject to the terms stated by the Bayerische Staatsbibliothek; consult the [digital source record](https://digitale-sammlungen.de/en/view/bsb00023199) before redistribution.
