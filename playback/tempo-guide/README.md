# Tempo guide for the viewer's player

Playback suggestions, not the edition's reading. DdT prints no metronome marks, and the MEI
carries no `@midi.bpm` or `@mm`, so Verovio's MIDI plays every work at ♩ = 120. These files give
the viewer's player a suggested speed for each tempo section, as a percentage of ♩ = 120; readers
change any section in the viewer, and the global Tempo % slider scales them all. Nothing here enters
the MEI.

One CSV per work, named by the viewer's work id (`op1_01.csv` … `app_03.csv`), one row per
tempo section:

| column | meaning |
| --- | --- |
| `measure_n`, `measure_id` | measure where the section starts (`@n` and `xml:id` in the assembled MEI) |
| `tstamp` | beat where it starts (1 unless the word stands later in the bar) |
| `text` | the tempo word as printed; two different words on one measure joined with " / " |
| `meter` | meter in force at the start |
| `suggested_percent` | suggested speed, % of ♩ = 120, rounded to 5 |
| `basis` | the rule below, or the reason for a value outside it |
| `tempo_ids` | `xml:id`s of every `<tempo>` mark the row stands for |

Every `<tempo>` in a work belongs to exactly one row: marks on the same measure (one per staff) are
one boundary, and so is the same word on the next measure's first beat (Op. I/5 mm. 175–176). Op. II/5
has no word before m. 120; its first row has an empty `text` and plays at 100 %.

## Rule (seeded 2026-11-01)

Quarter-note speed per word class, in 4/4 and 3/4:

| class | words | ♩ per minute | % |
| --- | --- | --- | --- |
| very slow | Grave, Lento, Largo | 50 | 40 |
| slow | Adagio | 56 | 45 |
| moderately slow | Poco Adagio, Saraband | 66 | 55 |
| moderate | Andante, Arioso, Arietta, Allamanda | 72 | 60 |
| fast | Allegro, Vivace, Courant | 100 | 85 |
| quite fast | Poco presto | 112 | 95 |
| very fast | Presto, Gigue | 132 | 110 |
| fastest | Prestissimo | 152 | 125 |

Then, from the meter and the note values of the original parts (violin, gamba, violone, continuo;
not the realization):

- 2/2 and 3/2: × 1.3; 6/8, 12/8, 3/8 and 6/4: × 1.2. Neither applies when 25 % or more of the notes
  are 16ths or shorter: then the 16ths set the pace and the 4/4 value stands.
- 4/4 and 3/4, fast words, fewer than 5 % 16ths: × 1.35 (a triple-time Allegro in eighths).
- Caps: at most 100 % when 25 % or more of the notes are 16ths or shorter (16ths at 8 per second),
  at most 50 % when 20 % or more are 32nds.
- Two different words on one measure: the slower class.

One value departs from the rule: App. III m. 1, Adagio in 2/2, 50 % instead of 60 %, so that its
32nds (6 % of the notes) stay at 8 per second.

38 of the 109 rows were flagged for a check by ear (compound or half-note meters, a slow word over
fast notes, a fast word without 16ths, the edge cases above). The editor listened to all 38 in the
viewer on 2026-11-02 and kept every suggested value; their `basis` ends in "ear-checked 2026-11-02".
The other 71 rows follow the rule unheard.
