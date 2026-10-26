# Jingyu Tu's recent edits: review of 2026-10-26

Reviewed remote `main` at `3cdae7fd52bbe39625a375341e30b72f6b78e975` after
`git pull --ff-only` reported that the checkout was current. This is a
repository cleanup audit, not publication sign-off or a new complete collation
of the edition.

## Findings and disposition

### Corrected: Op. I/3 m. 36 contains a duplicated A4 instead of E4

Commit [`7c2145b4`](https://github.com/egorpol/DdT_1_vol_11/commit/7c2145b49c2750b763857e42296559248a066500)
added `getgtd` as A4 to keyboard upper-staff chord `i59rtdc`, which already
contained A4 (`hdxo4my`) and C5 (`j16kmam6`). The resulting A4–A4–C5 reading
survived the subsequent review and the current validator accepts it.

DdT printed p. 23, BSB image 00033, m. 36, beat 3, shows E4–A4–C5.
The editor confirmed E4–A4–C5 on 2026-10-26, superseding the repeated-A4 reading
accepted in the 2026-10-19 review. Corrected `getgtd/@pname` from `a` to `e`,
retaining its ID, octave, inherited
eighth-note duration and layer. This restores the missing E4 rather than
deleting the added event. The complete musical XML differs only in that one
pitch attribute. Verovio playback changes that event from MIDI pitch 69 to 64
at the same time and duration. No emendation annotation is needed: this is an
OMR/encoding repair against the base source.

Source: [DdT, BSB image 00033](https://api.digitale-sammlungen.de/iiif/image/v2/bsb00023199_00033/full/4134,/0/default.jpg).

### Corrected: four existing event identities were replaced

In Appendix I m. 31, commit `176a2557` correctly separates the third-beat
keyboard realization into F4–G4 eighths and a B-flat3–D4 quarter-note chord in
layer 2. However, it removes the old chord and two note IDs and assigns new
ones to the surviving lower chord members. The source supports the musical
correction; the ID replacement is unnecessary under the
[event-identity rule](mei-encoding-profile.md#event-identity).

- Restored chord `tiyuv` in place of `ferfgrt`.
- Restored B-flat3 `suwyue` in place of `ghrh`.
- Restored D4 `utyuzp` in place of `fdghf`.

In Op. II/2 m. 218, commit `dded7e3e` replaces a quarter G4 with the printed
dotted-eighth F-sharp4 and sixteenth G4. Restored the old G4 ID `s1nvzsnv`
on the corrected sixteenth in place of `nghjnfg`; the supplied F-sharp4 keeps
its new ID `bhfgyy`.

These ID repairs leave both scores' rendered geometry and MIDI unchanged.
The removed Appendix I m. 24 rest `s3errc2` is different: DdT has a dotted
quarter in its place, so there is no surviving rest whose identity should
be restored.

### Resolved: redundant key definitions produced unprinted courtesy signatures

The thirteen Op. II/2 additions before mm. 219, 223, 227, 240, 251, 255,
259, 263, 266, 269, 272, 275 and 278 repeat the unchanged two-sharp key.
Verovio renders another five-staff key signature at the end of each previous
system. These courtesy signatures are absent from DdT.

A diagnostic copy with only these thirteen definitions removed validates
against the repository's MEI 5.1 CMN schema, retains 13 pages and identical
MIDI, and reduces rendered `keySig` groups from 355 to 290: 65 extra groups
come from these additions. Seven older definitions in this work produce
the same behavior. This is an engraving regression, not lost notes or a
changed sounding key. The subsequent corpus-wide cleanup removes all 77 redundant key declarations
across eight works, retaining their structural containers and IDs. All initial
keys, system-start signatures, measure placements and MIDI are preserved; 345
rendered signature groups disappear. See [the resolved issue](issues.md#unprinted-courtesy-key-signatures).
The diagnostic copy is local audit evidence, not a second edition.

### Aligned: Op. II/1 has completed work-level correction

The editor confirmed on 2026-10-26 that the previous session completed the
Op. II/1 correction. Its status is `corrected`; the older `combined` status
in the editorial manifest and planning text was stale. The README, current
work list and planning documents now agree. This does not add release
sign-off. Jingyu's recent commits do not edit this work, and the 203-measure
assembly is outside the attribution of the findings above.

## Scope and detailed dispositions

Inspected all 77 Jingyu Tu commits from 2026-10-18 through 2026-10-25,
comparing each changed file with its parent and the current score. These
are 30 commits for Op. I/3, 37 for Op. II/2, five for Op. II/7 and five for
Appendix I. Twenty-seven commits change only layer numbers. The two title
edits fill previously empty titles; they do not replace the later editorial
headers. No recent commit replaces a whole assembled file.

The older page-level correction history was screened for broad replacements
but was not re-collated note by note. Claims here about preserved content use
the completed work-level review commits below as explicit baselines.

### Op. I/3

Baseline: `0f7d89fa`, the 2026-10-19 source-review commit. All 246 measure
identities, numbers and facsimile pointers survive. The zones and surfaces
survive, and annotation `editorial.op1_03.m17.shared-notehead` retains its
attributes, content and targets.

- Retained the layer-number normalization, which changes staff-local voice
  labels from 5/6 to 1/2 without changing the notes or their IDs.
- Rechecked the surviving pitch corrections in mm. 73 and 92 against DdT:
  B4 in the violin and C5 in the keyboard chord are supported.
- Rechecked the figure position in m. 197 and the written C-sharp in m. 212;
  these are supported. The figure moves to the last sixteenth of beat 4.
- Retained the deliberate two-voice C4 at m. 17. Its shared-notehead issue
  is documented and differs from the accidental duplicate within one chord
  at m. 36.
- The historical m. 36 error described above remained present even in the
  baseline review. Comparison with a reviewed commit alone could not find it;
  the source and chord-content check did.

### Op. II/2

Baseline: `7f4ac0ce`, the 2026-10-19 source review. All 281 measure identities,
numbers, facsimile pointers, zones and surfaces survive. The m. 189
source-supported E3 eighth, its annotation and supplemental-material link
survive. The only formatting difference in that annotation is indentation
around its existing supplemental link. The two later mixed-meter encoding
notes are also present.

- Retained m. 6's figure at beat 3, m. 81's single `7♭`, and m. 154's
  closing figure at the last sixteenth of beat 2; checked against DdT.
- Retained the gamba stem changes at m. 183 and staff-5 layer normalization.
  No lower-keyboard layer now uses 5/6.
- Retained the cross-staff B3 in m. 197, dotted-eighth F-sharp4 plus
  sixteenth G4 in m. 218, and added F-sharp3 beneath the last B3 in m. 221;
  checked against DdT p. 97 or p. 99 as applicable.
- Retained the m. 246 figure at `tstamp="3.5"`. Jingyu's `tstamp="4"` was
  already repaired in `3cdae7fd`: in this 3/2 bar, 4 is the barline, whereas
  the source places the figure under the closing quarter note.
- The subsequent source corrections at mm. 210, 222 and 241 and the mixed
  12/8/common-time encoding notes have not been reverted.
- The thirteen key restatements were removed with the equivalent corpus-wide
  cases after verification; the system-start key signatures remain.

### Op. II/7

Baseline: `665232c9`, the 2026-10-20 completed review, after all five incoming
October edits. The later changes do not alter its 217 measures' notes,
durations or IDs; the differences from that baseline are removal of stale
`metcon="false"` markers.

Rechecked the m. 26 keyboard rhythm, m. 30 figured-bass continuation, m. 65
stack `6/3`, and m. 66 silent space against the DdT crops. These incoming
corrections remain supported. The title is still the full editorial title.

### Appendix I

Baseline: `3517d0d4`, the 2026-10-20 completed review. All 89 measure
identities, numbers, facsimile pointers, zones and four surfaces survive.
The eight repeated-strain sections and explicit expansion retain their
order. Playback still produces 178 measure occurrences: each written
measure twice. The m. 72 missing-dot conjecture and its annotation survive.

- M. 24: the violin dotted-quarter B-flat4 replaces a quarter plus eighth
  rest, following DdT p. 161. Retained.
- M. 31: the B-flat3–D4 quarter under the two F4–G4 eighths follows p. 161.
  Retained the musical correction and restored the existing IDs.
- M. 33: the lower keyboard layers are normalized to 1/2. Retained.
- M. 76: D4–G4–B-flat4 in the two tied keyboard chords and the continuo
  G2–G2 tie follow p. 163. Retained.

## Subsequent issue-register decisions

On 2026-10-26 the editor chose explicit first-page MEI title/composer headings
for all 17 scores, including standalone exports. All 17 headings preserve page
counts and MIDI; the authority-linked composer metadata remains intact.

The existing Op. II/4 ties and Appendix I repeat plan were rechecked and remain
correct. The editor chose to retain the source readings at Op. I/7 m. 250 and
Op. I/3 m. 17 with documented engraving limitations. Fresh controls still
reproduce those two limitations in the pinned renderer. The [issue register](issues.md)
distinguishes resolved edition issues from these accepted display limitations.

## Validation and review limits

- The repository tests pass: 49 tests.
- Refreshed all 17 tracked editorial reports with CAMAT 0.2.7 and Verovio
  6.3.0, including schema, Schematron, reference, duration, complete rendering
  and consumer parsing checks. All 17 pass MEI conformance and consumers;
  publication acceptance remains `needs-review`.
- The report set retains 286 findings: 276 warnings and 10 information
  entries. These include 181 IIIF Schematron warnings, 17 per-work reminders
  about those warnings, 78 underfull-layer diagnostics and 10 terminology
  findings. No new finding category was introduced by the cleanup.
- The viewer build includes all 17 scores and validates the four linked
  supplemental excerpts. A local headless check of the built viewer found
  every rendered measure matching its MEI measure and zone, no problems and
  no console errors in all 17 works; the published site is checked after
  deployment.
- The final refresh, after the Op. II/1 status wording was updated, ran with
  network checks (2026-10-26 17:22 UTC): all 17 reports pass MEI conformance
  and consumers with the same 286 findings.
- The m. 36 example shows why schema-valid XML and successful rendering do
  not constitute source proofing. The direct source checks cover 19 selected
  changed measures, not every note in the four works.

Machine-readable per-commit diffs, pre-edit scores, source crops, baseline
comparisons, render/MIDI checks, the courtesy-signature diagnostic and full
validation runs are kept locally under
`validation/runs/jingyu-review-20261026/` (ignored by Git). The tracked
per-score CSVs and `validation/editorial-reports.json` record the final
cleanup inputs and report hashes. No reviewer sign-off, release version,
publication status or release tag is added by this audit.
