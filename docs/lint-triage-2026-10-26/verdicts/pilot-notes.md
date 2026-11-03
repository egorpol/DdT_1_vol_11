# Facsimile triage notes

All 23 input rows were compared with their MEI context and all 16 distinct supplied crops. Shared-crop rows were judged together. Pitch names use scientific octaves. No MEI was changed.

## False-positive patterns

- **Cross-staff unison doubling (165):** the C4 in the keyboard bass and the C4 assigned to the upper staff are both printed. A cross-staff chord can represent separate voices at the same sounding pitch; duplicate-pitch detection needs to consider explicit note-level `@staff` and the printed voicing.
- **High continuo in alto clef (196–199):** the printed A4–B4–C5–B4 passage doubles the gamba. A fixed bass-role ceiling produces four alerts for one legitimate passage. Consider active clef and nearby instrumental doubling when ranking range alerts.
- **Blank position in a figure stack (20):** an empty upper `<f>` leaves the resolving 3 on the lower row after 6/4. Evaluate the whole `<fb>`, rather than treating each empty `<f>` as missing musical content.
- **Printed editorial question mark (21):** `(6?)` is exactly what DdT prints. Preserve editorial qualifiers and distinguish them from transcription placeholders.
- **Figures during bass rests (57–59):** the bass explicitly alternates eighth notes and rests, while the realization continues the harmony and the figures mark resolutions during rests. The 8, 6, and sharp occur exactly at the encoded times. A sounding bass note at every figure is not required; the preceding bass can remain the harmonic reference.
- **Octave transfer with clef change (51):** low E2 in bass clef precedes E3 in alto clef. The octave-displacement heuristic catches a legitimate register change.
- **End-boundary direction (352):** `tstamp=7` in 6/4 anchors a direction after six quarter-note beats, at the final barline. A direction at the boundary need not satisfy the same strict bounds as a note onset.

## Encoding issues and printed anomalies

- **Incorrect gestural accidentals (1, 71):** the supplied lint spellings are backed by erroneous MEI `@accid.ges` values, rather than a resolver-only error: C-flat5 in row 1, G-sharp3 at the tie destination in row 71. The print gives natural C and G respectively. Do not dismiss conflicts merely because an accidental is gestural.
- **Missing octave (70):** the printed note is F-sharp4; adding `@oct="4"` is sufficient under the existing one-sharp key signature.
- **Tie endpoint copied from the other chord tone (72):** both encoded ties end on B4. The print ties the lower G4 to the next bar’s lower-voice G4 (`eegrz45`).
- **An unflagged gestural-accidental error (ALSO, 165):** gamba `rtcjck1` has `accid.ges="s"`, but the print gives E4 without a sharp in a one-sharp key. The flagged duplicate chord itself is faithful. The preceding bar also contains suspicious E-sharp metadata (`drqjkuq`), but its note is outside the supplied crop and was not judged.
- **Repeated keyboard omission already in DdT (261–263):** continuo/gamba flats on E are explicit or carried within their respective staves; neither keyboard staff prints the corresponding flat. The MEI accurately preserves this discrepancy. These are not resolver-only alerts. The print may assume an unusually implicit transfer of accidentals from the original parts to the realization, or may simply omit required flats; no normalization is proposed.
- **Ambiguous harmonic significance, clear transcription (25, 27):** the flat over B-flat and the stacked 6/sharp over D both agree with the MEI, as do the unaltered thirds in the realization. Their musical interpretation or a source-specific figuring convention remains uncertain. Both are marked printed readings with possible misprints and medium confidence; correcting the realization would go beyond the facsimile evidence.
- **Doubled engraved head (400):** enlargement shows adjacent heads at the C5 level on the same stem above G4, matching the duplicated MEI C5. This unusual engraving is marked a possible printed defect with medium confidence; an independent higher-resolution reproduction could clarify its intended chord.
- **Printed octave oddity (19):** the high G5 at the start of beat 4 is present in the scan. It may be a printed octave error, but the MEI reproduces it.

## Existing editorial exception to literal facsimile transcription

In the measure for row 20, violin `jov0yhc` is an eighth note in the MEI and a sixteenth in DdT. Its existing `source-supported-emendation` annotation explicitly documents that choice, citing the historical Op. I witness through the STIMU 1991 facsimile. This is recorded as an **ALSO** discrepancy, not silently treated as a literal reproduction and not proposed for reversal. The flagged figure-stack verdict is independent of this documented editorial policy exception.

Only the four flagged encoding errors have proposed fixes in the CSV. Their edits, and the additional E-sharp issue in row 165, require the editor’s decision and revision entry; none has been applied.
