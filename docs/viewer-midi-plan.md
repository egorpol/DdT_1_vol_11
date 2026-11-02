# MIDI playback in the viewer: plan

Status: plan of 2026-11-01; the editor's decisions are in section 7. Steps 1 and 1b (section 8) are
built, with the page-turn timing of 2026-11-02 (section 4.5); the push and the check of the live site
remain. Scope: the live viewer at
<https://egorpol.github.io/DdT_1_vol_11/> (`site/viewer.js`), then the sister viewers of webern_op27
and DdT 1, vols. 29/30. All numbers below were measured on 2026-11-01 with Verovio 6.3.0 (the
version the viewer loads) unless marked otherwise.

## 1. What the viewer gets from Verovio

The viewer already holds one work at a time in a Verovio toolkit (`breaks: 'encoded'`, one rendered page
per printed DdT page). The same toolkit can produce the audio data and the time map; no second toolkit
and no reload is needed.

| call | result on the 17 works | cost (wasm, headless Chromium) |
| --- | --- | --- |
| `renderToMIDI()` | base64 Standard MIDI File, 52–86 K characters; type 1, 6–7 tracks; 295–509 s per work, 6,524 s for all 17 | 224 ms (Op. I/1) – 380 ms (Op. II/3) |
| `renderToTimemap()` | 2,097–2,810 events per sonata; keys `tstamp`, `qstamp`, `on`, `off`, `tempo` | 21–34 ms |
| `getElementsAtTime(ms)` | `{page, notes}` | ~0.7 ms per call (1,000 calls 692–751 ms) |
| `getTimeForElement(id)` | a note's or a measure's start in ms (measure ids work: 0 / 80,000 / 342,000 ms for three measures of App. II) | — |
| `setOptions({midiTempoAdjustment})` | rescales MIDI and time map together; 0.5 doubles both (443.5 → 887.0 s on II/3); no reload, rendered SVG unchanged | re-render 243–358 ms |

Channels and instruments come out as decided in `ba16e55a`: one channel per part, GM program 40
(violin), 42 (viola da gamba), 43 (violone, App. III), 6 (harpsichord) for the figured bass and,
on a channel of its own, Stiehl's realization (channel 3; channel 4 in App. II, which has two violins).
No percussion channel. Every work plays at Verovio's default of 120 quarter notes per minute, because the
MEI carries no `midi.bpm` or `mm` (DdT prints no metronome marks; decision of 2026-10-28).

**Repeats.** Verovio plays repeats from an `<expansion>` element or, when there is none, from an
expansion it builds from the repeat barlines. It builds none in a file with editorial markup ("An
expansion cannot be generated with editorial content"); in this edition that markup is `<annot>`.
The three works with printed repeats therefore carry an explicit `<expansion>`: App. I since
2026-10-26 (the automatic expansion crashed, Verovio #4533), Op. II/2 and II/3 since 2026-11-02
(they have 3 and 2 `<annot>`; an earlier version of this plan wrongly named `<app>`). Measured by
MIDI length (native 6.3.0, ♩ = 120): App. I 322.0 s with its repeats, 161.0 s without; II/2 668.7 s
(each of the Arietta's 20 four-measure strains twice, the first from the double bar at m. 150),
508.7 s without; II/3 488.5 s (mm. 218–232 twice), 443.5 s without. A check of every double, final
and repeat barline against the DdT pages (2026-11-02) found no repeat signs in the other 14 works;
Op. II/5 ends with an optional "Da capo se piace." that the player does not play. The viewer's
Repeats checkbox (on by default, remembered; shown only for these three works) sets Verovio's
`expandNever` when off, which applies at `loadData`, so the work reloads; the score is unchanged.

## 2. How Verovio-based projects play MIDI

From a web-research run (Codex, 2026-11-01) that read each project's current source at the commit
named; "not found" means not found in that code, not proven absent.

| project (commit) | player and samples | follow and page turn | mute / tempo / seek |
| --- | --- | --- | --- |
| Verovio book, MIDI chapter | MIDIjs, an unversioned script hosted at midijs.net; sound bank and licence not stated | `getElementsAtTime` in the player's callback (up to every 100 ms); `renderToSVG(page)` when the page changes | not found |
| Verovio editor and App (verovio-editor `3a0213f`) | html-midi-player 1.5.0 + Magenta 1.23.1 + Tone 14.7.58; Magenta's `sgm_plus` samples from Google Storage | 50 ms interval, `getElementsAtTime`, a page event; ids of repeated passages mapped back to the notated ids | not found |
| Verovio Humdrum Viewer (`cd10c8a`) | WildWebMIDI with one Freepats piano patch for every part | `getElementsAtTime(t − 600 ms)` from synthesis progress, page load, system scroll | seek only |
| mei-friend (`b5976af`) | vendored html-midi-player 1.5.0 bundle, `sgm_plus` | note-on events matched against the time map; `getPageWithElement` and a page update | seek from a selection; no mute, no tempo |
| Kitodo.Presentation (`e4849e4`) | html-midi-player with an oscillator, `sgm_plus` or a configured sample URL | not found | the player's seek bar |
| Edirom Online (`3e6da32`) | recorded audio only, no MIDI synthesis | — | — |

What this means here:

- Every project follows the music through Verovio's time API (`getElementsAtTime` or the time map), the
  approach of 4.2. Both calls are current in Verovio 6.3.0, not deprecated.
- None offers a switch per part or a live tempo control. The html-midi-player family routes sound by
  GM program, so two parts on the same program cannot be muted apart; this edition needs exactly that
  (continuo and realization are both GM 6).
- The samples of the most common stack (`sgm_plus`) carry no licence the research could find, and
  MIDIjs names no bank. An edition that states the licence of everything it shows needs a sample set
  with a stated licence (section 3).

## 3. Player stack

The viewer has no build step and no npm (section 7, "where the code lives"), so a stack must load as
pinned files from jsDelivr, as Verovio does. Versions, licences and APIs from the research run; sizes
measured 2026-11-01 as jsDelivr's compressed transfer.

| stack | code licence, transfer | part mute | live tempo | seek | samples |
| --- | --- | --- | --- | --- | --- |
| A. Tone.js 15.1.22 + @tonejs/midi 2.0.28 + smplr 1.1.0 | MIT; 67 + 10 + 39 KB | one smplr instrument per channel, own gain | `Transport.bpm`, notes scheduled in ticks | Transport position | rendered MP3 packs (below) |
| B. smplr 1.1.0 `Sequencer` + @tonejs/midi 2.0.28 | MIT; 39 + 10 KB | `muteTrack` | `bpm` | `position` | as A |
| C. js-synthesizer 1.13.0 (FluidSynth 2.4.6 in wasm) | BSD-3 wrapper, LGPL-2.1 engine; 8 + 187 KB | filter note events (no mute call) | `setPlayerTempo` | `seekPlayer(ticks)` | any SF2; we host an extract |
| D. SpessaSynth 4.4.2 | Apache-2.0 | channel mute | `playbackRate` | `currentTime` | SF2/SF3/DLS |
| E. html-midi-player 1.6.0 + Magenta 1.23.1 | BSD-2 / Apache-2.0 | none (routes by program) | none on the element | `currentTime` | `sgm_plus`, no licence found |

smplr 1.1.0's module imports nothing else and its build contains the `Sequencer` with `muteTrack`
(checked). D needs a bundler by its own browser guide and depends on `spessasynth_core: "latest"`, so a
no-build site would carry a bundle built once by hand. E cannot mute continuo and realization apart.

**Samples.** The FluidR3_GM pack in Benjamin Gleitzman's midi-js-soundfonts (one `<instrument>-mp3.js` per GM
program, base64 MP3 per note) is "Released under Creative Commons Attribution 3.0 license" by its README;
its source, FluidR3_GM.sf2, was released by its author Frank Wen under MIT (both checked). Musyng Kite,
the pack smplr loads by default, is out: Gleitzman says CC BY-SA 3.0, a distributor says CC BY-NC-SA 4.0.
For C, GeneralUser GS 2.0.3 (own licence, allows use in software and local copies; 32.3 MB whole) or
FluidR3 (MIT) would be cut down to the four presets this edition uses (6, 40, 42, 43); that extract's
size is not measured.

Measured on all seven FluidR3 files (2026-11-02): every sample is 3.13 s long, 88 notes
per file. Organ and strings sustain to the cut; piano and harpsichord have mostly decayed by then.
In the 17 works' Verovio MIDI (ties merged, each note at its onset's tempo-guide row, first-pass
section starts), 250 of 48,067 string notes (violin, gamba, violone) and 864 of 58,040 keyboard
notes (continuo 195, realization 669) outlast 3.13 s at 100 % of the guide; at 50 %, 1,054 string
and 3,259 keyboard notes do. The earlier figures (5 of 48,066 at 100 %, 36 at 75 %, 192 at 50 %)
were measured at a flat ♩ = 120 before the guide; the same probe at that flat tempo reproduces
5 and 192. smplr's looped sustain would cover long notes but is marked experimental
("can produce clicks"). File sizes (uncompressed): violin 2.87 MB, cello 3.01 MB, contrabass
2.15 MB, harpsichord 2.33 MB; a sonata loads three, 8.2 MB, about 5.6 MB on the wire
(violin 1.90 MB with brotli from jsDelivr).

**Hosting.** jsDelivr serves the Gleitzman files pinned to a commit (`044fab8e`: HTTP 200, full file,
`Access-Control-Allow-Origin: *`; checked), so the viewers can load them like Verovio, with an SRI hash
per file, instead of copying 10.4 MB into each repository or hot-linking the unversioned
gleitz.github.io.

**Chosen (editor, 2026-11-01): stack A, samples from jsDelivr pinned to `044fab8e`.** Tone.js, @tonejs/midi
and smplr load on the first Play from jsDelivr at exact versions with SRI hashes; one smplr `Soundfont`
per MIDI channel with `instrumentUrl` set to the pinned FluidR3 file for its GM program (never smplr's
default gleitz.github.io); its output goes through a gain per channel, which is the part switch. The
sample layer sits behind the module's interface, so C's SF2 loops can replace it later if listening shows
the cut notes matter (section 6).

## 4. Design

### 4.1 Data flow

1. Nothing loads until the first press of Play (the Web Audio context needs a user gesture anyway, and
   most visitors read rather than listen). Then the player code and the instrument samples load, and
   `renderToMIDI()` plus `renderToTimemap()` run on the work on show; the result is cached on the work's
   model (`model.midi`, `model.timemap`), so switching works and back costs nothing.
2. The notes are scheduled on Tone's Transport in ticks. Guide boundaries and encoded MIDI tempo
   events set `Transport.bpm` at their scheduled tick; global Tempo scales the effective speed live,
   and audio and highlighting rescale together,
   with no MIDI re-render. The position is kept in quarter notes: `Transport.ticks` / PPQ against the
   time map's `qstamp`, one clock for sound and highlighting (Cursor's drift risk). Checked 2026-11-01
   (@tonejs/midi on the viewer's Verovio output in headless Chromium; Verovio writes PPQ 120 and one
   tempo event, ♩ = 120 at tick 0, in all 17 works): every note's ticks / PPQ is a time-map `qstamp` in
   16 works, App. I with its `<expansion>` included; in Op. I/6, 51 notes start less than one tick before
   theirs (tick 31239 = 260.325 against 260.333). The player therefore matches with a tolerance of one
   tick and needs no `midiTempoAdjustment` fallback.
3. A work switch, or `loadData` of another work, stops playback first; the toolkit holds one document.

### 4.2 Highlighting and page follow

- A `requestAnimationFrame` loop reads the Transport's position in quarter notes (`Transport.ticks` /
  PPQ) and steps an index through the cached time map sorted by `qstamp`, never by `tstamp`, whose
  milliseconds hold only at 100 %: `on` ids get the class `is-playing`, `off` ids lose it. No toolkit call
  per frame (`getElementsAtTime` costs ~0.7 ms; at 60 frames per second that would be avoidable work).
- App. I plays from its `<expansion>`, and the time map names the second pass's notes by copies
  (2,441 of its 4,882 `on` ids, such as `xtb3m2h-rend2`). Each maps back to its notated id: the id
  itself if the MEI has it, else the id without its `-rend<n>` suffix, else `getNotatedIdForElement`.
  Checked 2026-11-01 against the MIDI pitches at each `qstamp`: 594 of the 599 second-pass events match
  (the other 5 are ties across the repeat); `getNotatedIdForElement` alone matches 537, and for 43 ids
  it returns an id that is in neither the MEI nor the SVG.
- Fragments drawn after a system break carry the class `id-<xml:id>`; the existing `svgNodes(id)`
  already finds both, so a tied note continued on the next system lights up in both places.
- Page follow: the viewer's model maps each note to its measure and each measure to its page
  (`model.ids`, `model.measures[...].page`), so the loop calls `showPage(page)` when the first sounding
  note's page differs from the one on show. `showPage` re-renders from the SVG cache and turns the
  facsimile; after a turn the loop re-applies `is-playing` to the notes still sounding.
- Facsimile: the playing measure's zone on the scan gets `is-playing` (the zones already exist for hover
  and pin), so a reader can follow the 1903 print as well as the rendering. `drawZones` rebuilds
  the zones after the scan decodes and on every resize, so the player re-applies the class after each
  `drawZones` call, not only after a page turn.
- CSS: one new colour token for `is-playing`, distinct from hover, pinned, noted and annotated; the
  pinned measure keeps its colour while playing.

### 4.3 Controls

A Playback checkbox in Settings is off by default and remembered. While off, the entire player
is hidden and Space keeps its normal page-scroll behaviour. Switching off stops playback and
invalidates any pending library or sample load; switching on shows the controls without loading audio.
The group contains Play/Pause, Stop (back to the start point), "m. 37 / 186", global Tempo (slider
and a % box, 25–200), and exclusive Parts and Tempo guide menus.

- Play starts at the pinned measure, else at the first measure of the page on show, else at the start.
  Play after Pause resumes where it paused, unless a different measure was pinned meanwhile: then it
  starts there. Stop returns to the start point.
- Seeking is pinning: click a measure, press Play (while playing, a click pins and the next Play jumps
  there). A measure's start is the `qstamp` of the time-map event at `getTimeForElement(measureId)`,
  and the Transport is set to that position in ticks.
- The position line is one element, `#player-position` ("m. 37 / 186"), for readers and for
  `check_site.py`.

Each Parts row has a sound select: Encoded (with its sample instrument name), Piano, Harpsichord,
Church organ or String ensemble. All parts applies one choice to every part, or Encoded to reset;
it shows Mixed when sounds differ. Choices are viewer settings remembered by role in
`ddt-viewer-sounds`; the MEI and MIDI keep their encoded instruments. Parts reads
"Parts (sounds changed)" while a non-encoded sound is in use. A file outside the current work's
encoded set needs consent before any request: the line under the select gives its size and jsDelivr,
with Allow download and Cancel. Cancel restores the previous sound. Agreement is remembered per
file in `ddt-viewer-sound-consent`, or just for the visit with a warning if storage is blocked.
All parts asks once for its file; Harpsichord never asks in this edition, since every work's
realization uses it. Restoring a choice without consent shows the line and Play uses encoded.
Changes during playback load in the background with Loading… beside the select; playback continues,
later attacks use the latest selection, and old voices finish on their old sound (including attacks
already in the 0.3 s horizon). Mute and volume act on their shared channel gain, including tails.
Failed loads keep the previous sound and report the reason. Stale loads, Stop, a new Play and work
switches cannot apply an obsolete swap. Replaced Soundfonts are disposed when their last voice ends;
decodes serialize per channel, and a work switch keeps a channel's decoded sound when the next
work uses the same one.

Data for the part switches: `scripts/build_site.py` adds per work a `parts` list to `works.json`
(`channel`, `label`, `role`), read from the MEI `<instrDef midi.channel>` and the staff roles in
`validation/editorial-works.json`; labels follow one rule: the MEI `<label>` if it is not empty,
else a name from the role (violin "Violin", viola_da_gamba "Viola da gamba", violone "Violone",
figured_continuo_bass "Continuo"), with a final full stop dropped ("Violino." → "Violino"); five
ordinary staves have no label (Op. I/2 staves 1–3, the continuo of App. I and App. III). The realization is always one part named "Realization (Stiehl)" for
its two staves, in all 17 works. Reuse `build_parts` in `scripts/normalize_midi_data.py`, which already
makes one part per staff, with its channel, and merges the two realization staves into one. Muting acts on the part's MIDI channel; the remembered state is keyed
by role. Each part also has a 0–100 % volume slider and % box (default 100 %), remembered by
role independently of mute. Gain is linear amplitude: muted ? 0 : volume / 100. Unmuting restores
that level, including 0 %; All on turns every part on, the figured bass included, and preserves
levels. Gain changes ramp briefly. The figured bass (role `figured_continuo_bass`, "Cembalo" or
"Continuo") starts muted until the reader ticks it, with a note in the Parts menu: Stiehl's
realization doubles it (97.2–99.8 % of its notes at the same onset and pitch, per work). The %
boxes apply on Enter, on leaving the box or on the spin arrows, and clamp to the slider's range.

The Tempo guide menu beside Parts says "Tempo guide: playback suggestions, not the edition's
reading." and "Each section in % of ♩ = 120; Tempo scales them all." It lists each section's
measure and tempo word, synced number and slider fields (25–200 %), and a reset to its suggestion.
Only changes are stored, per work and measure id; resetting deletes the change. The rows scroll
inside a capped panel with the label above them. Copy my tempo changes exports changed sections
across every work in work/measure order as CSV; if clipboard writing fails, a read-only text field
shows the CSV for manual copying. The separate review page and this Copy button support the editor's
ear check of the guide files.

The build embeds checked guide rows in `works.json`; the viewer never fetches CSVs. The cached
notated-position time map places each boundary in every repeat pass, including a jump into the
middle of an earlier section and boundaries inside bars. Seek applies the section at the start tick.
A boundary callback, which Tone runs up to 0.3 s before the boundary sounds (section 4.5), schedules
`bpm.setValueAtTime(bpm, time)` and records its section at once; the viewer hears of it on the
player's frame loop when the audio reaches the boundary. Live edits use the last callback that ran,
so Tone's lookahead cannot restore the earlier section; an edit in the 0.3 s before a boundary
therefore shows the next section's row up to 0.3 s early, while the sound changes on time. Multiple encoded MIDI tempo events override the guide (fields disabled with a note).
The global slider scales either map, with no MIDI re-render. Its note is "100 % = tempo guide",
"100 % = encoded tempo", or the single MIDI tempo as "100 % = ♩ 120".

Keyboard: Space toggles play while Playback is on, only when focus is not in a form control (the arrow keys keep turning
pages). The player is announced through the existing `aria-live` status line ("Playing from m. 37").

### 4.4 Licences and credits

The viewer's footer names the player library and the sound samples with their licences, as it already
does for Verovio and the BSB images; the README's licence section gets the same line. Nothing is
copied: the line credits Tone.js, @tonejs/midi and smplr (MIT) and the sounds as "FluidR3_GM by Frank Wen
(MIT), rendered as midi-js-soundfonts by Benjamin Gleitzman (CC BY 3.0)", with links to both licences. The footer
line ships with the player (step 1), since CC BY asks for credit wherever the sounds are used; the
README line follows in step 2.

Loading with SRI: Tone.js and @tonejs/midi as classic UMD scripts with `integrity`, as Verovio is loaded
now; smplr's module (no imports) fetched with `fetch(url, {integrity})` and imported from a Blob URL;
each sample file loaded through smplr's `storage` option, whose `fetch(url)` adds that file's
`integrity`. Tone and smplr share one native `AudioContext` (`Tone.setContext(ctx)`). Checked
2026-11-01 in headless Chromium: the violin file loads in 136 ms that way and a wrong hash is
rejected; a Blob URL in `instrumentUrl` loads too (160 ms). An integrity failure stops the player with
a message in the status line.

### 4.5 Timing and page turns (2026-11-02)

A page turn holds the page's main thread. Measured in headless Chromium, a first-visit turn took
46–116 ms on every page of the 17 works, and 281 ms (Op. I/4) and 347 ms (Op. I/1) under a 4× CPU
slowdown; `renderToSVG` is about half of it, the rest is inserting and decorating the page and
turning the facsimile. With Tone's default 25 ms lookahead, and smplr queueing notes on its own 50 ms
main-thread timer, notes due during that time started late: at Op. I/4's turn from p. 8 to p. 9,
9 of 605 sample starts (worst 42 ms) and, under 4×, 87 of 604 (worst 319 ms). The player now:

- hands notes to Web Audio 0.3 s ahead: Tone's `lookAhead` is 0.3 s, then `updateInterval` is set to
  0.025 s (the `lookAhead` setter sets it to half the lookahead, which leaves only 0.15–0.3 s);
- gives each smplr instrument a pass-through `Scheduler(context, {lookaheadMs: 2000})`, so a sample is
  started when Tone hands it over instead of waiting in smplr's queue;
- takes the audible position from `getTicksAtTime(currentTime)`, held at the start point until the
  Transport's start time, for the marks, Pause and the end of the work (`Transport.ticks` reads 0.3 s
  ahead, and right after a restart the previous run's position);
- delivers tempo and section notices on its own frame loop at audio time, dropping those of a replaced
  plan (Tone's `Draw` would drop a callback that is more than 0.25 s late);
- renders the next page's SVG in an idle task 50 ms after each turn and after Play, so the follow turn
  finds it cached;
- runs each note start and tempo boundary once (`once()`, `scheduleNote()`): Tone 15.1.22's Clock can
  process one tick in two updates (floating-point drift in `forEachTickBetween`; 2–4 ticks per 100 s
  of Op. II/2), and a note started twice left its first voice without a release, ringing for the whole
  3.13 s sample. Measured 2026-11-02 from Op. II/2 m. 150: 776 voices started and 776 released on the
  fixed build, against 8 never released before.

Measured 2026-11-02 at the same turn (probe in the git-ignored
`validation/runs/midi-player-build/tools/page-turn/`): 0 of 608 sample starts late, and 0 of 611 under
4×, with no `renderToSVG` inside either turn. For the reader, Play, Tempo and tempo-guide changes sound
about 0.3 s after the action; Pause, Stop, the part switches and the volumes act at once. A computer
slower than the 4× case can hold a turn longer than 0.3 s, so the viewer says that page turns may still
stutter there.

## 5. Build, tests and checks

- `scripts/build_site.py`: publish `parts` and validated `tempo` per work; copy `player.js` and
  the pure `tempo-map.js`. Validate CSV headers, measures and their order, first position, beat/meter,
  ownership and coverage of every tempo mark, matching words, and integer suggestions in 25–200 %.
  Missing CSVs fail for works with tempo marks; no marks and no CSV gives an empty guide. Report the
  file and row; never rewrite guide data. `tests/test_build_site.py` checks all 109 real rows,
  mid-bar offsets, part data and byte-identical site copies, plus rejection cases on temporary copies.
- `tests/test_tempo_js.py` runs `node --test` on each `tests/js/*.test.mjs` file when node exists (node 22 rejects a directory argument). Pure tests cover effective
  tempo plans (single/guide/encoded, global scaling, whole ticks), ordinary and mid-bar boundaries,
  repeat re-entry into a row measure or the middle of an earlier section, and duplicate suppression.
- `scripts/check_site.py` (Playwright, headless Chromium): keep all step 1 checks (one clock,
  highlights, page/scan follow, independent pin, pause/seek/stop, role mute, work-switch cancellation,
  live Tempo without re-render). Add fresh-context hidden player/Space/lazy loading, remembered
  Playback, switching off during a held sample load and successful retry, linear part gains and
  mute/0 %/All on independence, volume persistence and role remapping. Check Op. I/1's m. 27 → 28
  boundary (102 → 48 bpm), a slider edit during the boundary callback's lookahead (24 bpm), live
  section edits, reload, Copy and Reset, and seek into Lento. Check App. II's m. 51 beat 4 and
  App. I's repeat (Allamanda, 144 bpm at global 200 %). Open both menus at 390 px and the 11-row
  guide at 1400×1000; require no overflow, a panel inside the viewport and no console errors.
  Assertions read the documented `#player` data attributes, DOM controls and rendered marks.
  Headless Chromium tests state, not the sound heard by a listener.
- Page-turn timing (section 4.5), with a hook on `AudioBufferSourceNode.start` that records each sample
  start against `currentTime`: a sample-start margin of at least 250 ms (10th percentile) on Op. I/1;
  no start more than 5 ms late at Op. I/4's first-visit turn from p. 8 to p. 9, against a positive
  control (a 1 s block must make one start more than 50 ms late); Pause and Stop cancel samples already
  handed over; a restart after the end shows no previous-run position; tempo notices within a frame of
  their audio time, and a live edit inside the lookahead keeps its value; the next page rendered in its
  own task before the turn.
- Manual check in the user's Brave and on an iPhone (Safari's silent switch and autoplay rules).
- Pages rebuilds also watch `playback/**`. The browser check still runs locally before each push of
  viewer changes; it does not run in the Pages workflow.

## 6. Limitations to state in the viewer

- Repeats (App. I, Op. II/2 and II/3) plays each repeated strain twice; off plays the written order
  once (section 1). The optional Da capo at the end of Op. II/5 is not played.
- Each tempo section plays at a suggested percentage of ♩ = 120 from `playback/tempo-guide/`
  (rule table; the editor checked the 38 flagged rows by ear on 2026-11-02 and kept every value). Readers can change each
  suggestion and scale all sections with Tempo. These are playback suggestions, not the edition's
  reading; the MEI carries no tempo values.
- The figured-bass figures do not sound by themselves; the continuo plays the bass line, and the
  realization is Stiehl's 1903 right and left hand.
- General MIDI samples, not period instruments; no ornaments beyond what the MEI encodes as notes.
- Every sample stops after 3.13 s, so long notes end early, most audibly on organ and strings.
  At 100 % of the tempo guide, 250 of 48,067 string notes and 864 of 58,040 keyboard notes
  (continuo 195, realization 669) outlast it; at 50 %, 1,054 string and 3,259 keyboard notes do
  (Verovio MIDI, ties merged, onset's guide row, first-pass section starts; measured 2026-11-02).
  The earlier figures (5 of 48,066 at 100 %, 36 at 75 %, 192 at 50 %) used a flat ♩ = 120
  before the guide existed; repeating that flat-tempo probe reproduces 5 and 192.
- Play from a measure, or after Pause, starts every note held across the start point again from its
  attack: smplr 1.1.0 has no per-note sample offset. 696 of 3,568 measure starts (19.5 %) have such a
  note (Verovio MIDI, ties merged; measured 2026-11-01). A restarted harpsichord note also restarts its
  decay. Kept by the editor 2026-11-01 over dropping held notes (Codex and Cursor agreed).
- Play, Tempo and tempo-guide changes take effect about 0.3 s late, because notes are scheduled ahead
  so that page turns do not interrupt them (section 4.5); on a slow computer page turns may still
  stutter. Nothing loads before the first Play; then the libraries and the samples of the work's
  instruments load from jsDelivr (about 5.6 MB for a sonata's three). Piano needs another
  1.7 MB (raw 2.63 MB), Church organ 1.7 MB (raw 2.80 MB), String ensemble 1.8 MB
  (raw 2.80 MB); each asks before its own download. The browser keeps the files in its cache
  (`max-age=31536000, immutable`); clearing the cache can require another fetch. Each Soundfont
  decodes 88 samples of 3.13 s into AudioBuffers, tens of MB per part. The active sound and old
  voices occupy memory until disposed; trying sounds does not retain all the decoded instruments.
  Loading and decoding during playback can stutter on a slow computer.

## 7. Decisions

Second opinions (Codex and Cursor, `delegate ask --agent both`, 2026-11-01) agreed on all four
questions below, and the editor chose as they did (2026-11-01). Questions and answers:
`validation/runs/midi-player-plan/` (git-ignored). The follow-up decisions below supersede the
original tempo and part-control details.

| question | both picked | risks they raised (to build in) |
| --- | --- | --- |
| Tempo control | **percentage slider** (25–200 %, default 100 %) of the encoded tempo or of Verovio's ♩ = 120; one value, remembered; maps to `Transport.bpm` (4.1; `midiTempoAdjustment` only as fallback); same control in all three viewers | say beside the slider what 100 % means (♩ = 120, not the Allegro or Adagio of the print); compound meters (6/8, 12/8) and 3/2 still run on a quarter-note clock; 100 % keeps Webern I's encoding error, which needs its own fix |
| Start point and follow | **Play from the pinned measure**, else the first measure of the page on show, else the start; notes coloured, the playing measure's zone outlined on the scan, score and facsimile turn with the music; a manual turn or click stops following until the next Play; a click still pins | keep the playback cursor separate from the pin (calling `pin()` per measure would overwrite the start point and the URL hash); re-apply highlights after each page replacement; scan loading must never hold up the audio clock |
| Part switches | **one checkbox per part** in a small Parts menu, MEI labels plus "Realization (Stiehl)", all on by default (figured bass off since 2026-11-01, see below), remembered by role across works | the realization's two staves are one part, so one checkbox; store the role, never the channel (channels follow score order and differ between works, e.g. App. II); show remembered "off" states clearly and offer "all on". `docs/mei-encoding-profile.md` already promises that a player can mute either continuo or realization |
| Where the code lives | **one self-contained `site/player.js`**, copied identically into each repo, wired from `viewer.js` | `build_site.py` copies an explicit file list (add `player.js` in every port); no edition constants inside the module; document its interface; stop playback and clear pending work before a work switch |

Player stack and sample hosting (section 3), asked 2026-11-01 after the research run; the agents split, and the editor chose A and the pinned
jsDelivr files:

| question | Codex | Cursor | risks they raised (to build in) |
| --- | --- | --- | --- |
| Player stack | **C**, js-synthesizer with a self-hosted SF2 extract: real loops, so no note stops short at any tempo | **A**, Tone.js + @tonejs/midi + smplr: the only no-build stack with a gain per channel for mute, a live `Transport.bpm` and Transport seek, all as pinned jsDelivr files | C: a mute must silence notes already sounding, not only drop new note-ons; an extract without GM 0 does not serve Webern, so the SoundFont must be configurable. A: the 3.13 s cut (the original 5-note count used a flat ♩ = 120 before the guide; see section 3); drive the highlighting from the clock that drives the audio, or score and sound drift |
| Sample hosting (A, B) | **self-host** in each repository: the edition controls the bytes and their continued publication | **jsDelivr pinned** to Gleitzman's commit `044fab8e` with SRI, like Verovio; no 10.4 MB copy per repository | self-host: `build_site.py` copies an explicit file list, so the samples need their own copy step. jsDelivr: override smplr's default base URL (gleitz.github.io). Both: credit CC BY 3.0 (Gleitzman) and MIT (Wen), even when nothing is copied |

Follow-up decisions after listening, 2026-11-01. Questions and answers are in
`validation/runs/midi-player-build/followup-asks/` (git-ignored).

| decision | agreement | evidence folder |
| --- | --- | --- |
| Playback switch, off by default, remembered; switching off cancels pending loads | Codex and Cursor agreed | `validation/runs/midi-player-build/followup-asks/` |
| Volume per part, linear 0–100 %, mute independent; All on preserves levels | Codex and Cursor agreed | `validation/runs/midi-player-build/followup-asks/` |
| Tempo guide seeds from the rule table, with flagged rows checked by ear | Codex and Cursor agreed | `validation/runs/midi-player-build/followup-asks/` |
| One CSV per work, checked against the MEI by the build and embedded in works.json | Codex and Cursor agreed | `validation/runs/midi-player-build/followup-asks/` |
| Tempo guide menu beside Parts, editable sections and global Tempo scaling | Codex and Cursor agreed | `validation/runs/midi-player-build/followup-asks/` |
| Review page plus a Copy button for the editor's ear check | Codex and Cursor agreed | `validation/runs/midi-player-build/followup-asks/` |
| 2026-11-02: sound select per part and All parts (encoded, Piano, Harpsichord, Church organ, String ensemble); consent per extra sample file; background hot swap with old tails finishing | Codex and Cursor agreed on the consent and hot-swap picks; editor chose all three | build brief, 2026-11-02 |
| Figured bass muted by default, with a note in Parts; % boxes beside the Tempo and volume sliders | editor's request while listening (no agent ask) | `validation/runs/midi-player-build/tools/bass_doubling.py` |

## 8. Implementation steps (one session each)

1. **Player module and wiring in this viewer** (stack A, section 3; delegate build from this plan as the spec): `site/player.js`,
   `viewer.js` wiring, CSS, the footer credit, `build_site.py` parts, tests, `check_site.py` checks. Gates: tests, review
   gate, `check_site.py`, a cross-vendor review, the user's listening check in Brave. Hand off after the
   review, before docs.

1b. **Playback switch, part volumes and tempo guide** (2026-11-01 follow-up): build-checked CSV
   guides embedded in works.json, remembered controls, repeat-aware tempo scheduling, Copy for the
   ear check, node tests and extended browser checks. Verify tests, static build, JS syntax, review
   gate and full `check_site.py`; leave guide data and release notes for their own steps.

1c. **Page-turn timing** (2026-11-02): section 4.5, with its checks in `check_site.py` and node tests
   in `tests/js/player-timing.test.mjs`.

1d. **Sound choice and consent** (2026-11-02): per-role and All parts selects; per-file consent
   before extra requests, including restored choices; background hot swaps with shared channel gains,
   stale-load cancellation and disposal after old voices end. Pure-rule and resource-lifecycle node
   tests, request-counting/failure/360 px browser checks K1–K7, and corrected sample-duration figures.

2. **Docs and release notes** (README viewer section and licence line, CHANGELOG Unreleased/Added), push,
   Pages check on the live site.
3. **Port to webern_op27.** Prerequisite: movement I's `scoreDef/@midi.bpm="40"` makes Verovio play
   ♩ = 40, but the print's mark is dotted ♪ = 40, which is ♩ = 30 (movement I plays a third too fast:
   60.7 s instead of ~81 s); fix the data in webern's own MIDI step first. II (♩ = 160) and III
   (half = 80, played ♩ = 160) agree with their marks. Piano only: no part switches.
4. **Port to DdT 1, vols. 29/30.** Prerequisite: every part there still has `midi.instrnum="0"` (piano;
   Pisendel 40 `instrDef`s, Hasse 6) and no tempo values; port `scripts/normalize_midi_data.py` with that
   edition's staff roles and decide its instruments first (own session, editor's decision).
