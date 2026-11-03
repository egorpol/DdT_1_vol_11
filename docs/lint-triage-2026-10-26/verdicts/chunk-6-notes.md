# Chunk 6 facsimile triage

111 input rows, covering 62 distinct crops, were inspected. Verdict totals: 80 encoding_error, 17 printed_reading, 14 lint_false_positive. No MEI files were changed. Row ids below refer to the input CSV, not measure numbers.

## False-positive patterns

- **Alternating bass octaves:** rows 150, 151, 152, 153, 154, 155 reproduce the printed octave patterns. An isolated leap out and back is insufficient evidence of a wrong octave, particularly in the doubled continuo/keyboard bass.
- **Adjacent suspension and resolution figures:** rows 158, 159, 160, 320 print `4♯`. The 4 is a suspension and the sharp indicates the succeeding third; treating the sharp as an alteration of the fourth invents A♯, D♯ or G♯. The printed realization supplies the resolution.
- **Seventh plus a separate accidental third:** rows 156, 161 print `7♭` over G♯. The natural F seventh and lowered third belong to diminished-seventh harmony; applying the flat directly to the seventh invents F♭.
- **Empty stack slot:** row 29 has an empty upper `<f>` over the printed lower 3. This is a spacing slot, not a lost figure.
- **Resolver/key signature:** row 18 reports B4 natural, although the keyboard note is unaltered B4 under a one-flat signature, hence B♭4. Preserve staff, octave, key signature, child accidental, voice-sharing and incoming-tie state separately when resolving pitches.
- **Literal editorial doubt:** rows 22, 23, 24, 26, 28 contain question marks actually printed by DdT, including `6(♯?)`, `6 ?`, `♮ 4 ?`, `6?`, and `4?`. These are printed_reading, not transcription placeholders.

## Issues shared by rows

- Numerous A/C flats, and a few F/G/E alterations, are unfounded `@accid.ges` values: the inspected print has no sign or same-position antecedent. These are encoding errors, not resolver false positives. The paired clash and gestural reports share one fix: 2/427, 3/428, 4/434, 5/435, 6/439, 7/440, 8/441, 9/442, 10/443, 12/447, 15/449, 16/450, 17/452, 139/517, 140/518, 141/522, 142/524, 146/527, 147/528. Rows 436/437, 444/445, 450/451, 519/520 and 525/526 each identify separate notes in one measure with the same unsupported alteration. Row 143 inherits the erroneous flat from the preceding tied note reported in 142/524.
- Op. I/6 m10: rows 134, 157, 515 share the missing opening keyboard G♯4 sign (`newg001`). The final keyboard G♯4's gestural sharp is justified by that printed same-position antecedent. The separate B♯2 discrepancy in row 135 is printed, not a proposed correction.
- Op. I/6 m13: rows 137/516 share an unsupported flat on the final continuo B3 after an explicit B3 natural. The gamba's B♭ against the other parts is already in the print (row 136).
- Op. I/6 m127: rows 144/145 share a missing written sharp on the first lower-keyboard C3; it carries to the second C3.
- Op. I/6 m180: rows 148/162 share a missing printed violin C♯4. Row 149 is a separate spurious written sharp on the final keyboard D4, not an accidental carried from C.
- Op. II/4 m211: rows 314/324 share the missing printed violin A♭5.
- Op. II/4 m10 and m14: rows 317/318 place figures at the opening rest or wrong bass note; the print places them at beats 2 and 3 respectively.
- Op. II/4 m160: rows 322/323 share the missing continuo G3 half note, currently a `<space dur="2"/>`; both figure timestamps are correct.
- Ties do not justify changing the print: row 163 has an added flat at the second tied C4; row 164 has an erroneous gestural flat at the natural B3 tie endpoint. Row 138 needs B natural at the printed incoming keyboard tie; that tie is itself absent from MEI and is noted in the CSV.

## Printed discrepancies and uncertainty

Rows 11, 13, 135, 136, 310, 311, 312, 313, 315, 316, 319, 321 preserve contrasting accidentals already present in DdT. Rows 310/321 and 319 may rely on an accidental intended across octaves; the CSV marks these medium confidence and possible misprints. Row 135's lower-keyboard sharp is anomalous against the other parts and is retained with medium confidence. The printed question marks are also retained.

The CSV's `ALSO:` notes record clear additional mismatches in the inspected measures. Accidentals encoded as child `<accid>` elements were checked as well as note attributes. The only source-supported emendation found in these three full work files concerns Op. I/1 m11 violin rhythm (`jov0yhc`); it does not overlap any suspect in this chunk and no reversion is proposed.
