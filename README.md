# DdT 1, Vol. 11: Dietrich Buxtehudes Instrumentalwerke

Work-in-progress MEI corpus for *Dietrich Buxtehudes Instrumentalwerke: Sonaten fuer Violine, Gambe und Cembalo*, edited by Carl Stiehl and published as volume 11 of *Denkmaeler deutscher Tonkunst*, first series.

The corpus is currently in the editing and cleanup phase. The repository keeps the page-level OMR data separate from the combined sonata-level MEI files, so that source-page cleanup and final work-level correction can be tracked independently.

The current MEI files are based on OMR data from the [musiconn.scoresearch](https://www.musiconn.de/services/musiconnscoresearch) project. The OMR-derived data is represented as single pages. The intended final version contains complete sonata-level MEI files with linked facsimile views.

All editorial work on this corpus is carried out in [mei-friend](https://mei-friend.mdw.ac.at/).

## Source

| Field               | Description                                                                                           |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| Composer            | Dietrich Buxtehude (GND:[118665685](https://d-nb.info/gnd/118665685))                                    |
| Title               | *Dietrich Buxtehudes Instrumentalwerke: Sonaten fuer Violine, Gambe und Cembalo. 11*                |
| Preferred title     | *Sonaten*                                                                                           |
| Editor              | Carl Stiehl (GND:[117245674](https://d-nb.info/gnd/117245674))                                           |
| Publication         | Leipzig: Breitkopf und Haertel, 1903                                                                  |
| Extent              | 1 score (VIII, 185 pages)                                                                             |
| Holding institution | Hochschule fuer Musik und Theater Muenchen, Bibliothek                                                |
| Shelfmark           | N2/X 1 DDT, 11                                                                                        |
| BSB-ID              | `991009385569707356`                                                                                |
| BV number           | `BV035347306`                                                                                       |
| WorldCat            | [`775063768`](https://search.worldcat.org/oclc/775063768)                                              |
| URN                 | [`urn:nbn:de:bvb:12-bsb00023199-0`](https://nbn-resolving.org/urn:nbn:de:bvb:12-bsb00023199-0)         |
| Digital facsimile   | [https://digitale-sammlungen.de/en/view/bsb00023199](https://digitale-sammlungen.de/en/view/bsb00023199) |

## Repository Layout

```text
.
├── .github/workflows/update-progress-grid.yml
├── docs/progress/page_grid.svg
├── README.md
├── scripts/update_readme_progress.py
├── 11_buxtehude_sonatas_final/
│   ├── buxtehude_op1_01_sonata_f_major_corr.mei
│   ├── buxtehude_op1_01_sonata_f_major_corr_consistency_report.csv
│   └── ...
└── 11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/
    ├── bsb00023199_00013_facs_zones.mei
    ├── bsb00023199_00014_facs_zones.mei
    └── ...
```

The repository currently has two main MEI data directories:

- `11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/` contains page-level OMR data derived from the BSB digitization. Progress in this directory is tracked anonymously by the generated page grid below.
- `11_buxtehude_sonatas_final/` contains combined sonata-level MEI files. These are tracked manually at work level because their editorial status depends on musical correction, metadata, and final validation rather than only page presence.

Files ending in `_consistency_report.csv` are temporary working files for inconsistency tracking during correction. They are not part of the final MEI edition and may be deleted after the corresponding sonata has been corrected and finalized.

The page-level OMR files follow this naming pattern:

```text
bsb00023199_<page-image-number>_facs_zones.mei
```

For example, `bsb00023199_00013_facs_zones.mei` points to the corresponding IIIF image:

```text
https://api.digitale-sammlungen.de/iiif/image/v2/bsb00023199_00013/full/4134,/0/default.jpg
```

Printed score pages and BSB image numbers are offset by ten. For example, printed page 3 corresponds to `bsb00023199_00013`; printed page 13 corresponds to `bsb00023199_00023`.

## Sonata-Level Files

The final sonata-level files use concise, sortable filenames:

```text
buxtehude_op<opus-number>_<work-number>_sonata_<key>.mei
```

Appendix works use:

```text
buxtehude_app_<work-number>_<short-title>_<key>.mei
```

Temporary working suffixes such as `_corr` may be used while a file is still being edited. Finalized files should use the clean names below.

Status values for the sonata-level files:

- `pending`: no sonata-level MEI file has been assembled yet.
- `combined`: page-level MEI files have been assembled into one work-level MEI file with linked facsimile surfaces.
- `corrected`: musical text and facsimile references have been corrected and local consistency checks have been reviewed.
- `finalized`: metadata/header, editorial review, validation, and repository naming are complete.

Work IDs use `Op. <opus>/<no.>` or `App. <no.>`. MEI files are `buxtehude_<stem>.mei` (see naming rules above).

| Work | Key | Pg. | BSB | MEI stem | Status |
| --- | --- | ---: | ---: | --- | --- |
| Op. I/1 | F | 3 | 00013 | op1_01_sonata_f_major | corrected |
| Op. I/2 | G | 13 | 00023 | op1_02_sonata_g_major | pending |
| Op. I/3 | A min. | 22 | 00032 | op1_03_sonata_a_minor | corrected |
| Op. I/4 | B♭ | 33 | 00043 | op1_04_sonata_b_flat_major | corrected |
| Op. I/5 | C | 44 | 00054 | op1_05_sonata_c_major | pending |
| Op. I/6 | D min. | 55 | 00065 | op1_06_sonata_d_minor | combined |
| Op. I/7 | E min. | 66 | 00076 | op1_07_sonata_e_minor | corrected |
| Op. II/1 | B♭ | 79 | 00089 | op2_01_sonata_b_flat_major | pending |
| Op. II/2 | D | 90 | 00100 | op2_02_sonata_d_major | pending |
| Op. II/3 | G min. | 103 | 00113 | op2_03_sonata_g_minor | pending |
| Op. II/4 | C min. | 116 | 00126 | op2_04_sonata_c_minor | pending |
| Op. II/5 | A | 126 | 00136 | op2_05_sonata_a_major | pending |
| Op. II/6 | E | 139 | 00149 | op2_06_sonata_e_major | pending |
| Op. II/7 | F | 150 | 00160 | op2_07_sonata_f_major | pending |
| App. I | — | 160 | 00170 | app_01_suite_to_op1_04 | pending |
| App. II | C | 164 | 00174 | app_02_sonata_2violins_gamba_cembalo_c_major | pending |
| App. III | D | 176 | 00186 | app_03_sonata_gamba_violin_cembalo_d_major | pending |

## MEI Header Policy

Final sonata-level files should carry a compact MEI header rather than the minimal OMR/transcoding header. The header should document the electronic MEI file, the historical source, the encoding process, the encoded work, and the meaningful file revision history.

The structure follows the [MEI Guidelines for metadata](https://music-encoding.org/guidelines/v5/content/metadata.html) and the [`meiHead`](https://music-encoding.org/guidelines/v5/elements/meiHead.html) element reference: `meiHead` contains `fileDesc` as required metadata, followed here by `encodingDesc`, `workList`, and `revisionDesc`. Within `fileDesc`, use `titleStmt`, `pubStmt`, and [`sourceDesc`](https://music-encoding.org/guidelines/v5/elements/sourceDesc.html) for the file title/responsibilities, publication or distribution information for the MEI file, and the historical source from which the MEI file is derived.

Modern project responsibility should be separated from historical source responsibility. Carl Stiehl is the editor of the 1903 printed source and should be recorded in `sourceDesc`. The student or researcher who reads and corrects the OMR should be recorded in `titleStmt` using `respStmt`, with a responsibility such as `OMR correction and editorial review`.

Keep the header intentionally lean. Avoid `xml:id` values in the header unless another element references them. Do not duplicate the same responsibility in both `titleStmt` and `editionStmt`. Keep application metadata concise, and use `revisionDesc` only for meaningful lifecycle events such as assembly, correction, and finalization.

Template for sonata-level files:

```xml
<meiHead xml:lang="en">
   <fileDesc>
      <titleStmt>
         <title>Sonata I in F major, Op. I: digital MEI edition</title>
         <composer>
            <persName auth="GND" auth.uri="https://d-nb.info/gnd/118665685" codedval="118665685">Dietrich Buxtehude</persName>
         </composer>
         <respStmt>
            <resp>MEI encoding and sonata-level assembly</resp>
            <corpName>CAMAT</corpName>
         </respStmt>
         <respStmt>
            <resp>OMR correction and editorial review</resp>
            <persName>Student Editor Name</persName>
         </respStmt>
      </titleStmt>
      <editionStmt>
         <edition>Corrected draft</edition>
      </editionStmt>
      <pubStmt>
         <publisher>CAMAT Corpus Editions</publisher>
         <date isodate="YYYY-MM-DD">YYYY-MM-DD</date>
         <availability>
            <useRestrict>MEI data released under the MIT License.</useRestrict>
         </availability>
      </pubStmt>
      <sourceDesc>
         <source>
            <bibl>
               <title>Dietrich Buxtehudes Instrumentalwerke: Sonaten fuer Violine, Gambe und Cembalo</title>
               <title type="series">Denkmaeler deutscher Tonkunst, first series, vol. 11</title>
               <composer>Dietrich Buxtehude</composer>
               <editor>
                  <persName auth="GND" auth.uri="https://d-nb.info/gnd/117245674" codedval="117245674">Carl Stiehl</persName>
               </editor>
               <imprint>
                  <pubPlace>Leipzig</pubPlace>
                  <publisher>Breitkopf und Haertel</publisher>
                  <date isodate="1903">1903</date>
               </imprint>
               <identifier type="URN">urn:nbn:de:bvb:12-bsb00023199-0</identifier>
               <identifier type="BSB-ID">991009385569707356</identifier>
               <repository>Hochschule fuer Musik und Theater Muenchen, Bibliothek</repository>
               <identifier type="shelfmark">N2/X 1 DDT, 11</identifier>
               <ref target="https://digitale-sammlungen.de/en/view/bsb00023199">Digital facsimile</ref>
               <biblScope unit="page" from="3" to="12">pp. 3-12</biblScope>
            </bibl>
         </source>
      </sourceDesc>
   </fileDesc>
   <encodingDesc>
      <appInfo>
         <application>
            <name>musiconn.scoresearch</name>
            <p>Source OMR data.</p>
         </application>
         <application>
            <name>mei-friend</name>
            <p>Manual correction and editorial review.</p>
         </application>
      </appInfo>
   </encodingDesc>
   <workList>
      <work>
         <identifier type="repository-stem">op1_01_sonata_f_major</identifier>
         <title>Sonata I in F major, Op. I</title>
         <composer>Dietrich Buxtehude</composer>
         <key pname="f" mode="major">F major</key>
      </work>
   </workList>
   <revisionDesc>
      <change isodate="YYYY-MM-DD">
         <changeDesc>
            <p>Combined page-level OMR files into sonata-level MEI.</p>
         </changeDesc>
      </change>
      <change isodate="YYYY-MM-DD">
         <changeDesc>
            <p>Completed musical correction and local validation.</p>
         </changeDesc>
      </change>
   </revisionDesc>
</meiHead>
```

## Current Progress

The following anonymous grid is automatically generated daily from the MEI files in this repository. It distinguishes pages that have mei-friend edit metadata, pages that are present but not yet edited, and page numbers that are currently missing from the image-number sequence.

<!-- progress-grid:start -->
![Anonymous page editing status](docs/progress/page_grid.svg)

Updated: 2026-06-18.

Current anonymous page status: 74 edited in mei-friend, 102 present but not yet edited, and 7 missing from the 183-page image sequence (176 MEI files currently present).
<!-- progress-grid:end -->

## Funding

Work on this corpus is funded by the German Research Foundation (DFG), program Library and Information Services - E-Research Technologies (LIS), grant PF 669/18-1.

## Citation

When citing this corpus, include both the encoded repository and the underlying source:

> Dietrich Buxtehude. *Dietrich Buxtehudes Instrumentalwerke: Sonaten fuer Violine, Gambe und Cembalo*. Edited by Carl Stiehl. Leipzig: Breitkopf und Haertel, 1903. Digitized by Bayerische Staatsbibliothek, `bsb00023199`.

Digital facsimile: [https://digitale-sammlungen.de/en/view/bsb00023199](https://digitale-sammlungen.de/en/view/bsb00023199)

## License

The MEI data and repository materials are released under the [MIT License](LICENSE).

The historical source is in the public domain, but reuse of the BSB facsimile images and metadata may be subject to the terms of the providing institution. Please consult the BSB record linked above for current reuse information.
