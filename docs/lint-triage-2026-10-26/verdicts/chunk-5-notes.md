# Chunk 5 facsimile triage

Reviewed all 108 input rows against all 63 distinct supplied crops and their MEI contexts. Related rows sharing a measure were judged together. Results: 77 encoding-error rows, 20 lint false positives, 11 printed readings. Counts are suspect rows, not independent corrections. No MEI was changed.

## Lint patterns

- **Resolutions during bass rests:** rows 60–62, 86, 88–90. The print places figures at the rests following short bass notes. The keyboard realization confirms continued harmony and suspension resolution. A figure need not coincide with an acoustically sustained continuo note.
- **Separate bare accidentals beside figures:** rows 55, 56, 91. The sharp alongside 4 or parenthesized alongside 6 specifies a separate sharp third, rather than an altered fourth/sixth. At row 56 the violin also carries its explicitly written C♯5 from beat 2; resolver results should respect that sign.
- **Prefix accidental qualifies a numbered interval:** row 87. Printed ♯6 over B means G♯, not D♯.
- **Interval quality versus absolute accidental:** row 94. Printed minor-third indication 3♭ above E♭ is fulfilled by G natural. Treating it as an absolute G-flat requirement creates a false conflict. Rows 82/92/491 show the complementary case: with the actual printed B-natural bass restored, 5♭ is F natural, not F flat.
- **Original editorial queries:** rows 68, 395. DdT really prints (♯?) and 8?, respectively. A question mark is not necessarily an unresolved transcription placeholder.
- **Empty stack slots:** rows 396–399. There is no upper printed figure at the flagged times; an empty `<f/>` keeps a lone lower figure/sign aligned with the preceding stack. Do not invent an upper figure. Row 396's lower digit is heavily ink-filled: the present 8 versus a possible 3 warrants a higher-resolution check, independently of the empty-slot flag. Row 399's lower 3 is also dark, hence medium confidence.
- **Bass octave idiom and chord voice selection:** rows 393, 394. The print confirms F2 followed by F3 in row 393. Row 394's A3 is an upper chord tone over continuing D3, not the bass jumping up and back.

## Encoding patterns and shared causes

- **Unsupported gestural sharps:** rows 30/454, 31/456, 35–36/458–461, 38/462–463, 46–47/466–469, 48/470–472, 49/473, 50/474, 73/475, 74/478, 455, 457, 464, 476, 477, 479. These alter notes with no printed accidental and no supporting same-letter sign. Repeated flags in a bar often reduce to one spurious alteration propagated through repeated notes. In row 457 the visible later sharp belongs to upper-voice C5, not the flagged lower-voice G4.
- **Unsupported gestural flats:** rows 76/482, 77/484–485, 78/487, 79/488, 80/489, 81/490, 82/92/491, 85/495, 480–481, 483, 486, 492–494. In rows 480–481 the actual printed flat belongs to B5, not C6.
- **Missing written accidental:** rows 32, 33, 52, 53 share the omitted sharp on opening gamba D4 (`kzpvlpq`). One written sharp repairs the pitch carry responsible for all four flags.
- **Spurious written natural:** row 40. The opening keyboard F3 has no printed natural; its key-signature F♯ agrees with the violin. Remove the accidental attribute on `kvi9i5d`.
- **Wrong pitch positions:** rows 39/465 encode a printed C♯4 as E♯4; the earlier C4 sharp supports the gestural sharp once the letter is corrected. Row 41 encodes the final gamba B2 as D3. Rows 42/63 encode the keyboard's final F♯3 and C♯4 as repeated E4s. Row 45 encodes continuo F♯3 as D3; its preceding quarter is also G3 in print, encoded E3. The latter is reported with ALSO. Row 50/474 also reports the keyboard's final printed F♯3 encoded D3.
- **Visual offsets encoded as musical time:** rows 65–67. Opening figures placed slightly left of whole-note basses have `tstamp="0.8"`; they belong at beat 1.
- **Missing figure staff association:** row 69. The figure is visibly under staff 3 and its bass is sounding. The missing `@staff` makes lint look up staff None.

## Printed discrepancies retained

Rows 34/54, 37, 43, 44/64, 75, 83/93, 84 and 392 reproduce discrepancies or omitted signs already present in DdT. Some are plausibly read through an accidental in another octave or another part; the CSV records the relevant signs and marks possible misprints without proposing changes. These are not encoding repairs.

No `source-supported-emendation` annotation occurs in the three full MEI files involved in this chunk. No such emendation was proposed for reversal.

## Verification

`python3 validation/runs/musical-lint/check_verdicts.py triage-out/verdicts.csv validation/runs/musical-lint/chunk-5-input.csv`

Result: `PASS: 108 verdict rows, 108 expected`.
