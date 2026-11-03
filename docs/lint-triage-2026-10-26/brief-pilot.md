# Facsimile triage of musical-lint suspects (DdT vol. 11, Buxtehude)

<task>
Each row of `validation/runs/musical-lint/pilot-input.csv` is a suspect that `scripts/musical_lint.py` found in one assembled MEI edition of Buxtehude's trio sonatas. The editions transcribe Denkmäler deutscher Tonkunst vol. 11 (1903). For every row, compare the MEI with the printed DdT page and decide whether the MEI encodes the print correctly. Write one verdict per row to `triage-out/verdicts.csv` in the worktree root.

The purpose is to find real encoding errors and to learn where the lint is wrong. The MEI must reproduce the print, so a row where the print itself is musically odd is not an encoding error.
</task>

<inputs>
- `validation/runs/musical-lint/pilot-input.csv`: columns `row` (the id to report), `work`, `page` (DdT page within the work), `measure` (MEI `@n`), `zone`, `staff` (`1+4` = two staves), `role`, `check`, `xml_ids` (the flagged MEI elements), `detail` (the lint's reading), `crop`.
- `validation/runs/musical-lint/<crop>`: a JPEG of that measure on the DdT page (BSB scan), padded about 200 px left and right, so neighbouring bars show partly; the bottom can show the next system's top, which is not part of the row. Staves run top to bottom in MEI staff order 1, 2, 3, … Rows that share a crop are the same measure: judge them together.
- `validation/runs/musical-lint/context/rowNNN.xml` (NNN = `row`, zero-padded to 3 digits): the MEI `<measure>` element(s) holding the flagged xml:ids. A comment above each gives the page, measure, meter, and the clef, key signature and role of each staff in force there. The full files are `11_buxtehude_sonatas_final/buxtehude_<work>_corr.mei`; read them when a row needs more context (a clef change, a tie from the previous bar, a key change).
- Staff roles (per `validation/editorial-works.json`): in most works staff 1 violin, 2 viola da gamba, 3 figured continuo bass (figures printed under it, encoded as `<harm><fb><f>` with `@tstamp`), 4 and 5 the keyboard realization that DdT prints (its editor's, not Buxtehude's, but part of the print we transcribe). Some appendix works differ; the context header names each staff's role.
</inputs>

<how_the_lint_reads_pitch>
The lint spells each note through CAMAT's resolver: key signature plus written accidentals (`@accid`, `<accid>`, `@accid.ges`) carried to the barline. A pitch in `detail` such as `Cb5` is that resolver's output, not necessarily what the MEI writes. When the MEI's own attributes and the key signature give a different pitch than `detail` (for example an accidental carried across octaves or staves), the row is a `lint_false_positive`; say "resolver" in `note`.

Checks:
- `accidental_clash`: two notes of the same letter with different accidentals struck together in different staves.
- `figure_accidental_conflict`: a figure's accidental (or an accidental figure such as `♭` alone = flat third) asks for a pitch that no sounding note honours. Check the figure text and the bass note against the print first.
- `figure_text`: the `<f>` text is blank, has `?`, full-width parentheses or an unusual sign; check what DdT prints there (a figure, a stacked figure, nothing).
- `figure_over_silence`: a figure's `@tstamp` falls where the bass staff has no sounding note; usually a wrong `@tstamp` or a missing/wrongly timed bass note.
- `octave_displacement`: an isolated leap out and back by about an octave; check the middle note's octave (`@oct`) and the clef.
- `tie_pitch_mismatch`: a `<tie>` or `@tie` joins notes of different pitch; check both notes and whether the print has a tie or a slur.
- `out_of_range`: a note outside a generous range for the role; check `@oct` and clef changes.
- `chord_duplicate_pitch`, `missing_pitch`, `tstamp_beyond_bar`: as named.
</how_the_lint_reads_pitch>

<reading_the_print>
Read the sounding pitch from the print as a player would: clef, key signature, and accidentals holding to the barline at the same staff position. If the print seems to follow another convention at that spot (an accidental meant to hold across octaves, a cautionary sign), say so in `note`. The scans are clear 1903 engraving, but small figures and accidentals can be ambiguous at crop resolution: lower `confidence` rather than guess.
</reading_the_print>

<output>
`triage-out/verdicts.csv`, UTF-8, comma-separated, quoted as needed, exactly these columns in this order, one line per input row, no other rows:

`row,verdict,page_reading,mei_reading,proposed_fix,misprint,confidence,note`

- `verdict`, one of:
  - `encoding_error`: the MEI differs from the print at the flagged spot.
  - `printed_reading`: the MEI matches the print, and the oddity is in the print itself.
  - `lint_false_positive`: the MEI matches the print and the music is fine; the lint's assumption failed (resolver, idiom, stacked figure, ...). Name the failed assumption in `note`.
  - `unclear`: the crop does not settle it; say what would.
- `page_reading`: what DdT prints at the flagged spot, in plain terms (e.g. "staff 4 beat 3: f♯' half note; figures under staff 3: 6, ♯").
- `mei_reading`: what the MEI encodes there (attributes, not the lint's spelling).
- `proposed_fix`: only for `encoding_error`: the smallest MEI change that makes it match the print, as `xml:id: @attr old -> new` (several separated by `; `). Never propose a change that makes the music "better" than the print.
- `misprint`: `yes` / `maybe` when the print itself looks wrong (only for `printed_reading`), else `no`.
- `confidence`: `high` / `medium` / `low`.
- `note`: short. If you notice a different clear mismatch elsewhere in the same measure, add it here prefixed `ALSO:`.

Also write `triage-out/notes.md`: false-positive patterns you saw with their row ids (input for tuning the lint), and any systematic encoding issue that spans rows.
</output>

<constraints>
- Do not edit any MEI or other repository file; only create `triage-out/`. Each real fix needs the editor's approval and a revision entry, so you report and they decide.
- Open every crop you judge; never infer the print from the MEI. Spend effort on looking, not on writing long notes.
- Done means `python3 validation/runs/musical-lint/check_verdicts.py triage-out/verdicts.csv validation/runs/musical-lint/pilot-input.csv` prints PASS.
</constraints>
