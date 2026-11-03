# Facsimile triage: chunk 1

Inspected all 58 distinct supplied crops for the 114 input rows. Shared-crop rows were judged together. No MEI was edited. Verdict counts: 82 encoding errors, 24 lint false positives, 8 printed readings. These counts are suspect rows, not distinct fixes.

## False-positive patterns

- **Independent accidental figures parsed as altered numbered intervals:** rows 204, 205, 206, 207, 208, 209, 213, 412, 416, 422. DdT places a number and an independent third-altering sign side by side, sometimes within a larger vertical stack. Thus `4♯` can mean fourth plus sharp third, and `7♭` can mean seventh plus flat third. The realization confirms the distinction. The parser should preserve figure grouping and allow an independent accidental rather than always attaching a sign to its adjacent digit.
- **Blank figure rows used for vertical layout:** rows 411, 414, 417, 418, 419, 420. The enclosing `fb` contains a real figure (3 or sharp); an empty/whitespace `f` above it preserves vertical alignment. Inspect the full stack before reporting missing text.
- **Alto-clef continuo outside generic role bounds:** rows 200, 201. A4 and B4 are clearly printed; the continuo temporarily occupies the upper register.
- **Legitimate register changes:** rows 202, 203, 408. The octave leaps are printed. Row 202 changes clef immediately after B2; row 203 also illustrates the danger of comparing events across bar/voice boundaries.
- **Parallel voices flattened into a melody:** row 409. The first violin has simultaneous dotted-half A5 notes in two voices; the sequence heuristic invents a leap between voices.
- **Incoming tie and accidental state:** row 173. The C-sharp tied from m54 into m55 plausibly remains in force for the subsequent C5. The resolver loses that continuation (medium confidence under the print's implied accidental convention).
- **Accidental continuing a preceding figure:** row 415. The sharp follows 6 and can refer to the sixth, supported by F-sharp in the printed realization. Treating every bare sharp as a new third is too restrictive (medium confidence).

## Systematic encoding issues

- **Unfounded gestural accidentals:** rows 529–574, together with clash rows 166–171, 175–176, 178–193 (where present in this input). Most are E-sharps with no printed sign or preceding alteration. Other examples are E-flats in m18 (531–534), D-sharp in m27 (539), G-sharp in m39 (541), B-flat in m70 (543), and A-sharp in m107 (545). These are encoding errors, not resolver false positives. Repeated rows in a bar share this cause; overlapping fixes should be applied only once. The tied first E4 in m128 (183) also has an unfounded sharp, inherited from the erroneous preceding E-sharp encoding.
- **Natural carried into/within a bar overridden by a gestural sharp:** rows 172/218 refer to the same F4 tied from m30 to m31; change `knl616u` to gestural natural. Rows 210/546 share an F4 whose written natural earlier in m109 remains in force; remove its gestural sharp.
- **3/8 timestamps counted in the wrong unit:** rows 214–217. Each flagged figure is placed at `tstamp=2`, but DdT aligns it with the final eighth at `tstamp=3`. This causes either apparent silence or comparison with the preceding bass pitch. In the appendix, row 421 is a separate half-beat timing error: the first parenthesized sharp belongs at 2.5 rather than 3.
- **Missing written sharps:** row 174 omits the gamba's parenthesized D-sharp. Rows 404/405/410 share the missing initial F-sharp on violin 2 in appendix m7; adding that first printed sharp also resolves the later repeated F.
- **Whole note encoded as measure rest:** row 413. Appendix m56 staff 4 prints C3 as a whole note; the encoded `mRest` creates the spurious figure-over-silence report.
- **Additional mismatch noticed in m4:** rows 204/529 notes flag `i19vy97o`: the second violin sixteenth is printed F-sharp4 but encoded G4. This is separate from the flagged E-sharp and figure parsing issues.

## Readings retained from DdT

Rows 177, 194, 195 omit a repeated sharp in a higher keyboard octave after a sharp in the lower octave. They may reflect octave-wide accidental scope in DdT; medium-confidence printed readings preserve the notation rather than silently adding signs. Row 189 lacks the keyboard C-sharp printed in the gamba, without a same-staff C-sharp to carry. Rows 406 and 407 also retain printed cross-part accidental discrepancies. Row 211 faithfully includes DdT's `♯?`; row 212 reflects the resulting questioned figure against unaltered A. These are not instructions to improve the print.

No flagged note in these two works was named by a `source-supported-emendation` annotation. The unrelated documented conjectural emendation in E-minor m38 was left outside this triage.
