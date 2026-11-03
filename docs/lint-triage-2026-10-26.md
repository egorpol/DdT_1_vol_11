# First musical-lint triage pass: record of 2026-10-26

On 2026-10-26 an AI model (OpenAI Codex) compared each suspect that
`scripts/musical_lint.py` listed in the assembled works with the DdT 1903 page
image and gave one verdict per suspect. The editor spot-checked eight verdicts
and then approved a fix list built from them. The resulting 351 corrections in
15 works were applied in commit
[`78347338`](https://github.com/egorpol/DdT_1_vol_11/commit/78347338aed5f03c6def984d8a85405a92508d73)
and released in 0.10.0. This file and the folder
[`lint-triage-2026-10-26/`](lint-triage-2026-10-26/) are the durable record of
that pass. The working files stay in the git-ignored `validation/runs/musical-lint/`.
The verdicts are model classifications, not a collation of the edition.

## Versions

- Suspects: `scripts/musical_lint.py` at commit
  [`444bc97c`](https://github.com/egorpol/DdT_1_vol_11/commit/444bc97c185b171f1dccca9fd45d84321c1dfa67),
  run on the works as they stood at that commit, against baseline tag `v0.9.0`.
  The commit changes only the script, so the MEI is that of `204bbe8e`. A re-run
  of the lint at `444bc97c` on 2026-11-03 gave the same 688 rows; only their order differed.
  The `row` ids are those of the triage input.
- Corrections: commit `78347338` ("Apply 351 musical-lint fixes in 15 works",
  2026-10-27), released in `v0.10.0` (`294166ac`). The changelog lists them per
  work under 0.10.0.

## Rows and runs

The lint listed 688 suspect rows. Two of them, rows 403 and 425
(`event_id_removed`: ids present in v0.9.0 but missing), have no page position
and were not triaged. The other 686 were triaged in two disjoint runs (no shared
row id):

| Run | Rows | Brief | `encoding_error` | `printed_reading` | `lint_false_positive` | `unclear` |
|---|---:|---|---:|---:|---:|---:|
| Pilot | 23 | `brief-pilot.md` | 4 | 7 | 12 | 0 |
| Main run, six chunks | 663 | `brief-template.md` | 482 | 74 | 105 | 2 |

- The main run's chunks hold 114, 109, 111, 110, 108 and 111 rows. Its six briefs
  equal `brief-template.md` except for the input file name. That template adds two
  things the pilot brief lacks: the `accid_ges_mismatch` check and a note on
  documented emendations.
- Main-run rows by check: `accid_ges_mismatch` 263, `accidental_clash` 199,
  `figure_accidental_conflict` 82, `figure_text` 48, `figure_over_silence` 38,
  `octave_displacement` 20, `tie_pitch_mismatch` 9, `out_of_range` 4.
- Of the 74 `printed_reading` verdicts, the model marked the print itself as a
  likely misprint in 5 (`misprint` = yes) and as a possible one in 64 (maybe).

## From verdicts to corrections

- Before approving the fix list, the editor spot-checked eight verdicts (commit
  message of `78347338`; release notes 0.10.0). No file records which eight.
- A local script built the fix list from two sources: the `proposed_fix` of every
  `encoding_error` row, from both runs, and the readings the model added after
  `ALSO:` in a row's `note`. All 482 main-run `encoding_error` rows feed the list.
  Rows with other verdicts contributed only through `ALSO:` readings.
- Several rows can lead to one correction, for example an accidental clash and a
  gestural-accidental row on the same note. One row can also lead to several
  corrections. Rows and corrections therefore count different units.
- Two applied corrections rest on pilot verdicts alone: Op. I/2, m. 142 (an
  octave) and m. 149 (a tie's end).
- Items that needed a page check or a new transcription were held back. The
  0.10.0 release notes list them under "Passages still awaiting a page check or
  re-transcription". The second pass took them up (CHANGELOG, Unreleased;
  [`lint-spot-check-2026-10-28.md`](lint-spot-check-2026-10-28.md)).
- 351 is `total` in `apply-summary.json`. The applier counts one correction per
  changed element and class, in 15 works. By class:

  | Class | Count |
  |---|---:|
  | Unfounded gestural accidental removed | 253 |
  | Figure moved to its printed onset | 39 |
  | Written accidental added | 21 |
  | Pitch corrected | 15 |
  | Written accidental removed | 8 |
  | Tie corrected | 4 |
  | Gestural accidental changed | 3 |
  | Gestural accidental made a written one | 3 |
  | Written accidental changed | 2 |
  | Rest or spacer replaced by the printed note | 2 |
  | Figure moved to another staff | 1 |

## Files in `lint-triage-2026-10-26/`

| File | Content |
|---|---|
| `brief-pilot.md`, `brief-template.md` | The instructions the model received. Their paths point into the git-ignored run folder. |
| `pilot-input.csv`, `chunk-1-input.csv` … `chunk-6-input.csv` | The rows as the model received them, without the `crop` column. Columns: `row`, `work`, `page` (DdT page within the work), `measure` (MEI `@n`), `zone` (facsimile zone id), `staff`, `role`, `check`, `xml_ids` (the flagged elements), `detail` (the lint's reading). |
| `verdicts/pilot.csv`, `verdicts/chunk-1.csv` … `chunk-6.csv` | The verdicts as returned. Join them to the inputs on `row`. |
| `verdicts/*-notes.md` | The model's notes for each run: false-positive patterns and suggestions for tuning the lint. |
| `apply-summary.json` | The applier's summary: per work and class, the count, the measures and the `xml:id`s. |

Not included:

- The measure crops the model looked at. The `crop` column named one JPEG per
  measure, cut from the BSB scans of DdT 1903. The `page`, `zone` and `measure`
  columns locate each row on the facsimile.
- The fix list and the other working files. The applied changes and their
  revision entries are in commit `78347338`.

## Limits

- The verdicts are one model's classifications from cropped page images. Apart
  from the editor's eight spot-checks, no person checked them.
- A verdict count is not a count of corrections. Neither count measures the
  accuracy of the edition.
