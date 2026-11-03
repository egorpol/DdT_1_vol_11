# Chunk 4 facsimile triage

Compared all 110 rows against all 62 distinct supplied crops. Shared crops were judged together. No MEI files were changed.

## Encoding patterns

- **Quarter-based figure timestamps in 6/8, Op. I/5:** rows 108–133. The figures and bass pitches are transcribed correctly, but the figures are placed too early. The meter unit is an eighth note: in this passage the usual conversion is `new tstamp = 1 + 2 * (old tstamp - 1)`. This accounts for both apparent silence and apparent accidental conflicts. The CSV gives the change for each flagged figure, without changing a sounding pitch. The other figures in these same bars need the same placement review (including rows 103/510, 104, 105 and 513/514). Exception: measure 118's second sharp, `b8e6oxoo`, is printed at eighth-note beat 4 but encoded at 3; do not mechanically convert it to 5. Row 109 notes this additional mismatch.
- **Unfounded gestural accidentals:** rows 103/510; 354/654; 355–356/655–656; 357/657; 358/658–660; 359/661; 360–361/664–667; 363/668; 365/669–670; 366/671; 367–368/672–673; 369/674–676; 370/677; 371/679; 372/682–684; 373/685–686; 662–663, 678, 680–681. These introduce sharps or flats absent from the page and unsupported at the relevant staff position. Repeated reports in a bar share this cause; the accidental-clash and gestural-mismatch rows sometimes propose the same change intentionally.
- **Wrong visible sign:** row 364. The gamba's A4 sign is a natural, encoded as a sharp. Fix the earlier written sign, not the later unsigned A4 flagged by the clash.
- **Missing visible sign:** rows 353 and 376 report the same missing keyboard A3 sharp (`pgllxo2`). The printed sharp matches the gamba and the parenthesized figure.
- **Incoming tie overrides the new bar's key:** rows 390–391. Both D naturals remain natural through the printed ties into measure 20; their targets incorrectly assert a gestural sharp.
- **Additional mismatch:** row 680's measure 178 has C-sharp3 in the keyboard bass where `e9jtby8` and `j1hqhy0x` encode B2. Reported with `ALSO:` in the CSV.

## Lint tuning and printed readings

- **Blank figure slots:** rows 375, 377, 381, 384–385, 388–389. Empty `<f>` elements preserve blank upper positions while the lower line continues with a number, accidental or dash. Do not treat every blank slot as missing figure text.
- **Figures during a bass rest:** rows 378–380. The print intentionally places 8/3 over a continuo quarter rest while the keyboard supplies the harmonic resolution. A sounding continuo note is not a prerequisite for a valid figure.
- **Valid unusual figure:** row 386. The printed cross is a double-sharp sign, correctly encoded as `𝄪`.
- **Intentional register leap:** row 374. The violin's low C-sharp5 followed by high C-sharp6 is present in the print; the leap heuristic alone cannot establish an octave error.
- **Cross-staff editorial accidental readings:** rows 511–512 read keyboard A3 as sharp from the gamba's printed A3 sharp; rows 513–514 read keyboard F4 as sharp from the violin F5 and bass F3 sharps. The keyboard notes themselves have no printed signs. These are `printed_reading`, with no reversion proposed.
- **Printed discrepancies, not encoding repairs:** rows 104–107, 362/383, 423. The printed realization has omitted/carrying accidentals or an explicit sign inconsistent with other parts/figures. Row 424 literally prints `5?`; the query is not an OCR placeholder.
- **Resolver caution:** where a plain note follows a written accidental, read the actual attributes and printed staff position before accepting the lint's spelling. In row 106 the keyboard A4 really does inherit the earlier written A4 sharp; this is a printed discrepancy, not resolver failure. No row here was dismissed solely by assuming that the resolver was wrong.

## Unsettled placements

- Row 382: the intervening sharp after 7 in Op. II/6 measure 48 is clear, but its precise onset relative to the dotted C-sharp3 and following F-sharp3 is not. A full-page spacing comparison or another facsimile rendering would help distinguish an early timestamp from a printed harmonic inconsistency.
- Row 387: the final 6-sharp in measure 131 may refer to F-sharp3 at eighth-note beat 6.5; it is encoded at 6 while G-sharp3 and keyboard E4 still sound. The crop does not establish the exact intended alignment confidently enough for a fix.

The source-supported emendation annotation in the E-major file concerns measure 3 (`y9d8tvb`), outside this chunk; no flagged note is covered by it.
