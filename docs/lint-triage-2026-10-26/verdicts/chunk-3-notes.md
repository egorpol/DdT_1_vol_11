# Chunk 3 facsimile triage

111 input rows were checked against all 54 distinct supplied crops, grouping shared measures. Verdicts: 89 encoding_error, 13 printed_reading, 9 lint_false_positive. Counts are suspect rows, not distinct notes or fixes; paired clash/gestural warnings frequently report the same error.

## Lint patterns

- Rows 101 and 241: a figure such as 4♯ or 7♯ can mean the numeral plus a sharpened third. The printed realization supplies F-sharp over D or G-sharp over E, respectively. Treating the sign as an alteration of the numbered interval produces a false conflict.
- Row 102: the flat and 5 are stacked. The flat belongs to the fifth (B-flat above E-flat), not to an implied third.
- Rows 349–350: full-width parentheses encode the printed parenthetical figures (7) and (6♯). They warrant typography normalization if desired, not a musical error.
- Rows 99 and 346: isolated-leap detection flags the engraving's repeated octave-changing figuration. Row 347 likewise prints the low E2 followed by E3, under a simultaneous G-sharp3 quarter. A three-note window mistakes this legitimate bass register change for displacement.
- Row 240: the G-sharp5/G2 scalar cross-relation is not evidence of an encoding error. The resolver/MEI takes an octave-wide reading of the earlier violin G4 sharp. Row 580 records that editorial accidental interpretation separately.
- Inspect child accidental elements as well as note attributes: row 98 correctly includes the printed B2 natural as child accid by1hpyn. Its clash against B-flat2 in the other bass staves is in the print.
- Rows 100, 239, 242, 243 and 348 preserve printed questioning or discrepancies. A figure/realization disagreement alone must not trigger a pitch correction. In particular, the printed sharp at row 348 is at F4, while the figure over B calls for D-sharp.

## Encoding patterns and shared causes

Unfounded accid.ges values are the dominant issue. Flat examples recur in the B-flat sonata (rows 496–509, with clash duplicates 95–97); sharp examples recur throughout the A-major sonata (especially rows 607–623 and 636–653). The signs are absent from the engraving, the key does not supply them, and no earlier alteration at that staff position supports them. A single bad first value is often copied onto every repetition in a bar: D4 in A-major measures 24 and 28, E3 in measure 187, and E4/E3 in measure 202. Remove the individually named unsupported attributes; do not introduce printed accidentals to justify them.

Rows 325/605, 326/606, 327/607, 328/611, 329/614, 330/616, 331/618, 332/621, 334/626, 335/627, 336/628, 339/633, 340/634, 341/637, 342/640, 343/643, 344/646 and 345/650 share flagged notes. Rows 238/577, 95/504, 96/505 and 97/508 likewise share their underlying hidden-accidental error. These must not become duplicate edits.

Row 333 is a different cause: an explicit MEI natural on G4 is absent from the print, which leaves G-sharp in force by key signature. The same bar's added C5 natural is noted in the CSV.

Rows 337 and 351 omit actual printed accidentals. Row 337's keyboard D4 natural is visible at enlarged crop scale; its gamba D4 sharps (rows 629–631) have a plausible editorial explanation in the earlier bass D3 sharp, across staff and octave. The print deliberately or inadvertently distinguishes the keyboard's natural; no gamba change is proposed. Rows 579–581 also retain plausible octave-wide interpretations of earlier same-letter signs, with medium confidence. Row 239's keyboard A3 is unmarked after A-sharp4, leaving an analogous ambiguity. These editorial readings need musical/editorial review, not automatic reversion.

## Other observations and protected reading

The CSV records additional clear mismatches in inspected measures with ALSO: row 100 (keyboard C3 encoded as B-flat2), row 328 (two printed ties absent), row 333 (extra C5 natural), and row 341 (missing written gamba D3 sharp).

Row 581's measure also contains y1dubf9q, the gamba E3 eighth. Its source-supported-emendation annotation explicitly retains the 1696 Op. II reading against DdT's quarter. This intentional departure is preserved, not proposed for correction.

No MEI was edited. The smallest proposed changes are reports for the editor; medium-confidence octave/staff accidental conventions remain explicitly identified in the CSV.
