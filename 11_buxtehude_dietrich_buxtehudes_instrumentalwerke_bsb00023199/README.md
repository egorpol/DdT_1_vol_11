# Page-level OMR files

One MEI file per BSB image of the DdT score, named `bsb00023199_<image-number>_facs_zones.mei`. The files began as optical music recognition (OMR) output from musiconn.scoresearch, with measure zones on the [BSB facsimile](https://digitale-sammlungen.de/en/view/bsb00023199), and were corrected page by page before the work-level files were assembled from them.

## Which files are authoritative

For every assembled work, the work-level file in [`../11_buxtehude_sonatas_final/`](../11_buxtehude_sonatas_final/) is authoritative. Corrections are made there. The pages of those works are kept as assembly input and provenance and are not updated with later corrections, so they can differ from the assembled score.

Op. II/1 (images 00089–00099) has not been assembled yet. Its pages are still the working files and are corrected here.

The page files are in neither validation work list, so the corpus checks do not cover them.

## Known issues in the preserved pages

Rechecked 2026-10-21. The assembled scores do not share these issues.

- Duplicate `xml:id` values, which make strict XML parsers reject the file: image 00023 (`d2qjhlp`, `i1p4r9x5`, `l4i9dkd`, `p1a251yb`), 00028 (`z1n4bkpv`) and 00049 (`r5xd43`).
- No measure zones: images 00036, 00106 and 00107. The assembled scores have 30, 16 and 16 zones on these pages.

Review these before using a page as standalone MEI or as input to a new assembly.
