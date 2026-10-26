# Encoding and rendering issues

Reassessed on 2026-10-26 with the pinned Verovio 6.3.0 runtime. Four edition issues are resolved: redundant key restatements, cross-layer ties, repeat playback and the composer heading. The editor accepted the two remaining engraving limitations on that date: tall figured-bass parentheses and the shared dotted C4 head. Their musical readings remain intact; this acceptance does not mean the upstream limitations are fixed. An open report is not a reason to change a source reading or file a duplicate.

## Unprinted courtesy key signatures

**Status: resolved in the edition, 2026-10-26.** Removed 77 redundant key
signature declarations across eight works: 49 `keySig` elements and 28
`scoreDef/@keysig` attributes. Each repeated the effective key already active
on every affected staff. The initial keys are retained, as are the
score-definition containers and their IDs, all clefs, meters and encoded breaks.
Retaining these containers also avoids shifting Verovio MIDI meter metadata.

All eight before/after comparisons preserve every system-start key signature,
page count, measure placement and MIDI bytes. The SVG output has 345 fewer
key-signature groups. Op. II/2 alone goes from 355 to 255 groups; its 51 systems
still begin with the key on all five staves. No notation event, annotation or
facsimile mapping changes. Full evidence and an illustrated comparison are in
local `validation/runs/courtesy-key-cleanup-20261026/`.

## Parentheses around a complete figured-bass stack

**Status: accepted engraving limitation; rechecked 2026-10-26.** This is tracked upstream as an MEI
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

**Recheck:** the pinned [Verovio 6.3.0](https://github.com/rism-digital/verovio/releases/tag/version-6.3.0)
runtime is `6.3.0-425dd7b`. The literal encoding still renders as the reported approximation.
Literal text around `fb` validates but, in the tested renderer, shows only the
parentheses and loses the figures. A `supplied` wrapper around `harm` validates
but renders the figures without a group enclosure. Proposed `@enclose="paren"`
on `harm`, `fb`, or `f` is rejected by both the repository's MEI 5.1 CMN schema
and the [current MEI development CMN schema](https://github.com/music-encoding/schema/blob/27b4bdd6c12b291f7b1f7d1dee73e6c9114f023d/dev/mei-cmn.rng)
(build 2026-09-28); the tested renderer also draws no enclosure for those
unsupported attributes. The Verovio development runtime was not tested.

**Edition decision, 2026-10-26:** the editor chose to retain the schema-valid
literal-parentheses reading and document its display limitation. Fresh controls
still reproduce the approximation; `enclose="paren"` on `harm`, `fb` and `f`
is still rejected by the pinned schema. MEI #619 and #1846 were read again and
remain open. No `supplied` wrapper is introduced because the editorial meaning
of the source parentheses remains unconfirmed. No viewer-only patch is applied.

**Resolution criterion:** a schema-valid encoding that preserves the source
meaning and renders one pair of parentheses spanning the complete stack. Until
then, retain the documented approximation and reassess against the existing
reports. Local reproductions are in the ignored
`issue_drafts/figured-bass-parentheses/` directory; the dated validation run
retains the fresh schema and rendering evidence. No new upstream report or
comment was submitted during this recheck.

## Cross-layer keyboard ties in Op. II/4

**Status: resolved in the edition; rechecked 2026-10-26.**
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

**Recheck, 2026-10-26:** all three explicit ties render as paths. MIDI contains
no new note attack at any of the three continuation-note onsets. Source
notation and event IDs are unchanged. These repairs complete the edition task;
classifying or reporting the former behavior upstream is optional follow-up.

**For the combined reassessment:** first isolate a schema-valid minimal example
with unchanged pitches, onsets and durations, compare inline attributes and
explicit endpoints, and search existing upstream reports. The current score
passes validation and renders all three connections; no musical emendation is
needed. Baseline and final evidence from 2026-10-19 are kept in local,
unpublished run directories.

## Automatic repeat expansion crashes on consecutive repeat endings

**Status: resolved in the edition; playback rechecked 2026-10-26.** In installed
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

**Recheck, 2026-10-26:** the current score exports MIDI successfully and its
timemap contains 178 measure occurrences, exactly two for each of the 89 written
measures. The four-page score and explicit strain order are retained. An
upstream report about the old automatic-expansion crash is optional follow-up,
not an unresolved correction in the edition.

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

## Dotted unison of a chord member and a single note

**Status: accepted engraving limitation; rechecked 2026-10-26.** In installed Verovio
`6.3.0-425dd7b`, a dotted-quarter C4 that inherits its dot from an
upward-stemmed C4–F4–A4 chord is drawn beside a downward-stemmed dotted-quarter
C4 in the second voice instead of sharing its head. The same chord without dots
and two single dotted notes both share the head. A schema-valid one-measure
reproduction without `sameas`, hidden notes or offsets gives the same result.

**Affected passage:** [Op. I/3, m. 17](../11_buxtehude_sonatas_final/buxtehude_op1_03_sonata_a_minor_corr.mei),
keyboard upper staff; DdT printed p. 22, BSB image `00032`. DdT prints one C4
head with stems up and down; the editor confirmed this reading. Persistent IDs
are measure `yttjgek`, chord `p1fgsraz` with its C4 `gdetgt`, and the second
voice's C4 `q15fei1p`.

**Current encoding:** both dotted-quarter C4 entries are retained with unchanged
pitches, durations and event IDs. Annotation
`editorial.op1_03.m17.shared-notehead` (`encoding-note`) points to both C4 events
and the chord. It describes the separated heads as an engraving limitation, not
a correction to the source reading.

**Issue search:** open and closed Verovio issues were searched on 2026-10-19.
The closest are [#746](https://github.com/rism-digital/verovio/issues/746),
dotted unisons of single notes in separate layers, fixed in 2018 (its
single-note case works in 6.3.0), and [#3705](https://github.com/rism-digital/verovio/issues/3705),
too many dots on unisons, closed in 2024.
[#3838](https://github.com/rism-digital/verovio/issues/3838), repeated pitches
with differing dots inside one chord, was closed as not planned. None reports a
dot inherited from the chord. The development runtime was not tested and no
report was submitted.

**Edition decision, 2026-10-26:** the editor chose to retain both dotted-quarter
C4 entries and document the rendering limitation. Seven fresh schema-valid
controls reproduce the result: explicit duplicate dot attributes align the
heads but introduce a warning and extra dot positions; the tested `sameas`
variants either leave the chord stem detached or lose the lower stem. The
ordinary two-note control merges correctly. The existing issue draft remains
local; no viewer-only patch or upstream submission is made by this cleanup.

**For the combined reassessment:** the reproduction, its controls, the DdT crop
and an issue draft are in the ignored `issue_drafts/shared-notehead-m17/`
directory. Recheck the then-current runtime and tracker before submitting it.

## Composer missing from Verovio's generated page header

**Status: resolved in all 17 scores, 2026-10-26.** The editor chose explicit MEI
page headings so the composer appears in standalone exports as well as the web
viewer. Every initial `scoreDef` now contains a `pgHead` with `func="first"`,
the edition title and Dietrich Buxtehude. Long appendix titles have a smaller
subtitle line. The metadata's GND-linked `composer/persName` remains intact.
The viewer's former temporary flattening of that metadata is removed.

All 17 candidate scores validate, render the composer on page 1, preserve their
page counts and export byte-identical MIDI. Full-page rendering is included in
the editorial report refresh. The [encoding profile](mei-encoding-profile.md)
now documents this choice. The public pre-release scope and edition versions
are unchanged.

[Verovio #4512](https://github.com/rism-digital/verovio/issues/4512), re-read on
2026-10-26, remains closed. The maintainer recommends explicit `pgHead` content
for editions rather than relying on automatic header generation from every
possible metadata structure. This is the approach now used here; no upstream
renderer fix is claimed.

Local evidence for the headings, accepted engraving limitations, and repaired
tie/repeat checks is in `validation/runs/issue-resolution-20261026/`.
