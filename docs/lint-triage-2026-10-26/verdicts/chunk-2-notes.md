# Chunk 2 facsimile triage

All 109 input rows were checked against their 65 distinct crops. Shared-crop rows were judged together. Counts describe suspect rows, not distinct corrections: 70 encoding_error, 26 lint_false_positive, 13 printed_reading.

## False-positive patterns

- **Empty upper figure slots are layout placeholders:** rows 220, 223, 227–234. The printed lower-row 4 or 3 is present in the following `<f>`; the empty `<f/>` preserves its vertical position.
- **Question marks belong to the edition:** rows 224, 288–291, 295–296. DdT actually prints `5?` or `6?`, sometimes as one member of a stack. Do not treat the punctuation as unresolved transcription.
- **Diatonic accidental figures over chromatically altered basses:** rows 226 and 294. The printed 7♭ over C♯ means B♭, a diminished seventh. The lint resolver lowers the signature B♭ again, while its interval-quality fallback does not recognize this diminished seventh.
- **Realization and passing tones:** row 222. The natural third is explicitly realized in staff 4, while the gamba briefly passes through E♭. The figure check reports any differently inflected note, even when another voice realizes the figure correctly.
- **High continuo register:** rows 282–283. Alto clef is correct, and the printed B♭4–A4 passage follows the gamba. The role's range bound is too narrow here.
- **Broken-register violin figures:** rows 284–287. All four low intervening notes are printed at the encoded octave. An isolated octave leap is not sufficient evidence of an octave error.

## Encoding issues spanning rows

- Numerous unfounded `accid.ges` values change unaltered printed notes: rows 245–247, 250–255, 257, 309, 582–603, with overlap between checks. These are actual pitch changes, not resolver false positives. Rows 401/687 and 688 additionally override an earlier explicit natural in the same bar. Shared warnings should be deduplicated by affected note/correction.
- In G-minor m43, row 248's printed G♯3 is encoded A♯3. The following printed A3 then carries an unjustified gestural sharp (row 249). The unrelated hidden G♭4 is covered by rows 250/586.
- Some printed signs are hidden or omitted: the A♮3 cancellation in row 256; A♭4 in rows 258/259/298; E♮4 in row 260; C♯5 in rows 264/301; E♭4 in rows 268/269/302; A♭4 in rows 270/271/303; E♭3 in rows 272/604; B♮4 in rows 273/305; E♭3 in rows 275/277; A♮4 in row 278; F♯4 in rows 279/308; cautionary F♮5 in row 281; and F♯4 in both parts in row 304. Several checks identify one omitted sign and its inherited effect on later notes.
- Rows 235–237 have wrong tie endpoints. The print shows ties between equal pitches. Row 236 also exposes an extra A4 at the next bar's start.
- Rows 225 and 293 have figures one eighth late/early respectively. Row 297 instead has the correct figure time but two missing continuo notes. Its proposed fix uses element replacement because the missing notes cannot be repaired by changing an existing pitch attribute.
- G-minor m231 has broader violin event errors (rows 279/280): the initial F♯4 sign is missing, the following printed F♯5 is encoded G5, later durations/pitches shift, and the final group is replaced by a space. Row 280 gives the printed sequence; its proposed attribute change addresses the flagged beat-9 note only. The editor should review the entire staff-1 bar before applying a revision.

## Printed readings and limits

Rows 219, 221, 244, 265–267, 274, 276, 292, 300, 306–307 and 402 preserve literal printed discrepancies. Their `misprint=maybe` records uncertainty about historical accidental conventions or intentional passing cross-relations, not uncertainty about whether the visible notes/signs were inspected. In particular, some keyboard realizations might expect an alteration implied by another octave or another part. No editorial harmonization is proposed.

Row 299 clearly adds an unprinted keyboard natural. The incoming E♭4 tie was checked in the full MEI (m200→201); the later violin E4's sounding interpretation depends on how that tie's alteration is carried through the bar. Removing the unprinted keyboard sign is the direct facsimile correction; any additional gestural clarification needs editorial judgment. Row 260's small natural sign was also inspected enlarged and is assigned medium confidence.

The source-supported-emendation annotations in the full input works were checked. The sole annotation found is Op. II/1 m114's gamba dot, outside these suspects; none of the proposed fixes reverses it. No MEI files were modified.
