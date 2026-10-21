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

## Cross-layer keyboard ties in Op. II/4

**Status: encoding repaired; upstream classification pending, 2026-10-20.**
The existing inline tie attributes did not resolve three printed connections
consistently in the installed Verovio 6.3.0 runtime. Explicit endpoints render
the source readings and remove the resulting warnings. This observation alone
does not establish an upstream bug; no issue search or report has been made for
this case yet.

**Affected passages:** [Op. II/4](../11_buxtehude_sonatas_final/buxtehude_op2_04_sonata_c_minor_corr.mei),
keyboard upper staff 4: C4 at mm. 110–111 (DdT p. 120), C4 at mm. 148–149
(p. 121), and B3 at mm. 164–165 (p. 122). Their endpoints have different layer
numbers. The previous encoding produced later warnings at unrelated notes in
mm. 141, 152 and 172. A separate, unprinted tie initial at m. 138 caused the
warning at m. 140 and was removed as an encoding error.

**Current encoding:** use `tie` elements with `@startid`, `@endid`, `@staff="4"`
and `@curvedir="below"`; retain every tied note and its printed duration. IDs
are `tie.op2_04.m110-111.c4`, `tie.op2_04.m148-149.c4` and
`tie.op2_04.m164-165.b3`. Annotation `editorial.op2_04.cross-layer-ties` records
the source evidence and encoding repair. This follows the
[MEI tie guidance](https://music-encoding.org/guidelines/v5/attribute-classes/att.tiePresent.html),
which permits an explicit `tie` element to specify visual information.

**For the combined reassessment:** first isolate a schema-valid minimal example
with unchanged pitches, onsets and durations, compare inline attributes and
explicit endpoints, and search existing upstream reports. The current score
passes validation and renders all three connections; no musical emendation is
needed. Baseline and final evidence from 2026-10-19 are kept in local,
unpublished run directories.

## Automatic repeat expansion crashes on consecutive repeat endings

**Status: reproduced; score encoding repaired, 2026-10-20.** In installed
Verovio `6.3.0-425dd7b`, Appendix I rendered normally but MIDI/timemap export
terminated with SIGSEGV in `ExpansionMap::CreateSection` / `Object::DetachChild`.
This also caused the CAMAT consumer check to crash. A schema-valid two-measure
reproduction, with each measure ending in `right="rptend"` and no intervening
explicit repeat start, has the same result. Adding an explicit start to the
second measure is a passing diagnostic control; that control is not an edit
to the edition's printed barlines.

**Affected work:** [Appendix I](../11_buxtehude_sonatas_final/buxtehude_app_01_suite_to_op1_04_corr.mei),
the four-dance suite on DdT pp. 160–163. Its former single section contained
eight repeated strains, with new dance starts and the Gique's second strain
implicitly beginning a new repeat span. The first repeat ending after such a
start could cause automatic expansion to reuse already detached children.
That mechanism is an inference from the backtrace, diagnostic control and
the inspected upstream implementation, rather than a maintainer diagnosis.

**Current encoding:** eight strain sections and one explicit `expansion`
listing each strain twice, in printed order. No printed repeat bar or source
break is changed. MIDI/timemap export now returns all 89 measures exactly
twice, in the intended strain order; all four score pages are pixel-identical
before and after this structural change. CAMAT parsing passes. The normal
MEI schema, reference, rendering and musical-diagnostics checks also pass.

**Issue search:** the public tracker was searched for repeat crashes and
expansion reports on 2026-10-20. The closest inspected reports were closed
[Verovio #1125](https://github.com/rism-digital/verovio/issues/1125), an older
crash involving an existing expansion element; closed
[#4258](https://github.com/rism-digital/verovio/issues/4258), requesting automatic
MEI expansion generation; and open
[#1300](https://github.com/rism-digital/verovio/issues/1300), broader expansion
enhancements. None of those descriptions establishes an exact duplicate for
this automatic-generation trigger. No development runtime was tested and no
upstream report was submitted.

**For the combined reassessment:** retain the two-measure reproduction,
passing explicit-start control, crash logs, issue-search responses and draft
in the local, unpublished run directory of 2026-10-20. Recheck the then-current runtime and tracker before deciding
whether to report the automatic-generation crash. The score's explicit
repeat plan is independently meaningful and does not suppress its repeats.
