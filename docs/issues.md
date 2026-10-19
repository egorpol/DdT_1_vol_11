# Encoding and rendering issues

Record upstream status, affected passages, and the current encoding here before
the planned combined reassessment. An open report is not a reason to change the
musical reading or to file a duplicate. Status dates refer to an actual recheck.

## Parentheses around a complete figured-bass stack

**Status: unresolved; rechecked 2026-10-19.** This is tracked upstream as an MEI
encoding request, with a remaining limitation in Verovio's rendering of the
available approximations.

- [MEI #619 — Parentheses on figured bass](https://github.com/music-encoding/music-encoding/issues/619)
  is open. Egor Polyakov's [comment of 2026-06-03](https://github.com/music-encoding/music-encoding/issues/619#issuecomment-4609801611)
  reports this exact Buxtehude passage, with source and rendering examples.
- [MEI #1846 — Allow `@enclose` on textual control events](https://github.com/music-encoding/music-encoding/issues/1846),
  opened by Egor Polyakov on 2026-10-13, is also open. It explicitly includes
  enclosure of a complete figured-bass stack through `harm` or `fb`.
- The [maintainer reply to #619](https://github.com/music-encoding/music-encoding/issues/619#issuecomment-4615543597)
  suggests wrapping `harm` in `supplied` when that represents the editorial
  meaning. It does not establish support for drawing one pair of tall
  parentheses around the stack. Parentheses alone do not establish that the
  figures were supplied; their meaning in this DdT passage has not been verified
  against another witness.

**Affected passage:** [Op. I/7, m. 250](../11_buxtehude_sonatas_final/buxtehude_op1_07_sonata_e_minor_corr.mei),
figured continuo, staff 3; DdT printed p. 76, BSB image `00086`. The older
page-level file numbers the same measure 47. Persistent IDs are measure
`ggk09au`, harmony `as8v3t`, zone `zone_1e02283eefa342fbb8`, and annotation
`editorial_bsb00023199_00086_as8v3t`. DdT prints one pair of parentheses around
the complete 6–4–2 stack.

**Current encoding:** retain literal outer parentheses, `<f>(6</f>`, `<f>4</f>`,
`<f>2)</f>`, with the source reading and upstream links in the annotation. This
validates, but the two parentheses remain beside the top and bottom figures
instead of enclosing the stack vertically. No pitches, durations, figures, or
source readings are changed to accommodate the renderer.

**Recheck:** [Verovio 6.3.0](https://github.com/rism-digital/verovio/releases/tag/version-6.3.0)
is the latest stable release checked; the installed runtime is
`6.3.0-425dd7b`. The literal encoding still renders as the reported approximation.
Literal text around `fb` validates but, in the tested renderer, shows only the
parentheses and loses the figures. A `supplied` wrapper around `harm` validates
but renders the figures without a group enclosure. Proposed `@enclose="paren"`
on `harm`, `fb`, or `f` is rejected by both the repository's MEI 5.1 CMN schema
and the [current MEI development CMN schema](https://github.com/music-encoding/schema/blob/27b4bdd6c12b291f7b1f7d1dee73e6c9114f023d/dev/mei-cmn.rng)
(build 2026-09-28); the tested renderer also draws no enclosure for those
unsupported attributes. The Verovio development runtime was not tested.

**Resolution criterion:** a schema-valid encoding that preserves the source
meaning and renders one pair of parentheses spanning the complete stack. Until
then, retain the documented approximation and reassess against the existing
reports. Local reproductions are in the ignored
`issue_drafts/figured-bass-parentheses/` directory; the dated validation run
retains the fresh schema and rendering evidence. No new upstream report or
comment was submitted during this recheck.
