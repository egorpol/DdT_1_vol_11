# Page-level OMR files

One MEI file per BSB image of the DdT score, named `bsb00023199_<image-number>_facs_zones.mei`. The files began as optical music recognition (OMR) output from musiconn.scoresearch, with measure zones on the [BSB facsimile](https://digitale-sammlungen.de/en/view/bsb00023199), and were corrected page by page before the work-level files were assembled from them.

## Which files are authoritative

For every assembled work, the work-level file in [`../11_buxtehude_sonatas_final/`](../11_buxtehude_sonatas_final/) is authoritative. Corrections are made there. The pages of those works are kept as assembly input and provenance and are not updated with later corrections, so they can differ from the assembled score.

Op. II/1 (images 00089–00099) was assembled on 2026-10-25 into `buxtehude_op2_01_sonata_b_flat_major_corr.mei`: 203 measures, 11 facsimile pages and 43 systems. Its proofread page readings are preserved; work-level review of the new consistency report remains pending. Further corrections belong in the assembled file.

The page files are in neither validation work list, so the corpus checks do not cover them.

## Recovered final measure of Op. II/1

Recovered 2026-10-22: image `00099` (printed p. 89) had 18 measure zones but only 17 encoded measures. Its last encoded measure contained both printed final bars: every nonempty layer had twelve quarter-note beats, divided at six in the source. The final measure's notes had not been deleted.

The boundary was already missing in the upstream `camat_corpus` raw `bsb00023199_00099.mei` at commit `f4729c6` (2026-04-08), before facsimile integration. The separate measure annotations correctly identified 18 bars; integration allowed a one-measure mismatch and retained the unused final zone. This repository imported that result in `fca6b533` on the same day; at the recovery's starting revision, `8d721e74`, the page had no intervening edits. The available files establish that the problem predates facsimile integration, but do not distinguish an OMR error from a MusicXML-to-MEI conversion error.

The repair separates page-local measures 17 and 18, preserves all existing musical event IDs and readings, moves the closing controls to measure 18, links it to `zone_947d646f5b714bc585`, and restores the printed final barline. Other OMR issues, including staff allocation, remain for correction against the source.

## Known issues in the preserved pages

Rechecked 2026-10-21. The assembled scores do not share these issues.

- Duplicate `xml:id` values, which make strict XML parsers reject the file: image 00023 (`d2qjhlp`, `i1p4r9x5`, `l4i9dkd`, `p1a251yb`), 00028 (`z1n4bkpv`) and 00049 (`r5xd43`).
- No measure zones: images 00036, 00106 and 00107. The assembled scores have 30, 16 and 16 zones on these pages.

Review these before using a page as standalone MEI or as input to a new assembly.
