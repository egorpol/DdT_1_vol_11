# MIDI playback in the viewer: plan

Status: plan, 2026-11-01; the editor's decisions are in section 7. Not implemented. Scope: the live viewer at
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
expansion it builds from the repeat barlines. Measured by MIDI length with and without the repeat
barlines (native 6.3.0): App. I has an explicit `<expansion>` (added 2026-10-26 after the automatic
expansion crashed, reported upstream as Verovio #4533, still open) and plays every strain twice
(322.0 s; 161.0 s without). Op. II/2 (39 repeat barlines) and II/3 (2) are not expanded: Verovio
refuses to build an expansion in a file with editorial markup ("An expansion cannot be generated with
editorial content"; both have 3 `<app>`), so their repeats play once until each gets an explicit
`<expansion>` as App. I did. That is an editorial data change outside this plan (HANDOFF, later
items). The other 14 works have no repeat barlines.

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

Measured on the FluidR3 pack: every note is one 3.13 s recording (88 notes each for violin, cello,
harpsichord); violin and cello hold full level to the end, so a longer note stops short, while the
harpsichord has decayed to −28 dB by then. In the 17 works' MIDI (ties merged), 48,066 notes are not
harpsichord; 5 of them outlast 3.13 s at 100 % tempo, 36 at 75 %, 192 at 50 %. smplr's looped sustain
would cover them but is marked experimental ("can produce clicks"). File sizes (uncompressed): violin
2.87 MB, cello 3.01 MB, contrabass 2.15 MB, harpsichord 2.33 MB; a sonata loads three, 8.2 MB, about
5.6 MB on the wire (violin 1.90 MB with brotli from jsDelivr).

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
2. The notes are scheduled on Tone's Transport in ticks, so a tempo change sets `Transport.bpm` (100 % =
   the encoded tempo, else Verovio's 120) during playback and audio and highlighting rescale together,
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

A player group in the toolbar: Play/Pause, Stop (back to the start point), the position as
"m. 37 / 186", the tempo control, and the part switches. Start point and follow behaviour, tempo control and part switches as decided in section 7.

- Play starts at the pinned measure, else at the first measure of the page on show, else at the start.
  Play after Pause resumes where it paused, unless a different measure was pinned meanwhile: then it
  starts there. Stop returns to the start point.
- Seeking is pinning: click a measure, press Play (while playing, a click pins and the next Play jumps
  there). A measure's start is the `qstamp` of the time-map event at `getTimeForElement(measureId)`,
  and the Transport is set to that position in ticks.
- The position line is one element, `#player-position` ("m. 37 / 186"), for readers and for
  `check_site.py`.

Data for the part switches: `scripts/build_site.py` adds per work a `parts` list to `works.json`
(`channel`, `label`, `role`), read from the MEI `<instrDef midi.channel>` and the staff roles in
`validation/editorial-works.json`; labels follow one rule: the MEI `<label>` if it is not empty,
else a name from the role (violin "Violin", viola_da_gamba "Viola da gamba", violone "Violone",
figured_continuo_bass "Continuo"), with a final full stop dropped ("Violino." → "Violino"); five
ordinary staves have no label (Op. I/2 staves 1–3, the continuo of App. I and App. III). The realization is always one part named "Realization (Stiehl)" for
its two staves, in all 17 works. Reuse `build_parts` in `scripts/normalize_midi_data.py`, which already
makes one part per staff, with its channel, and merges the two realization staves into one. Muting acts on the part's MIDI channel; the remembered state is keyed
by role.

Keyboard: Space toggles play only when focus is not in a form control (the arrow keys keep turning
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

## 5. Build, tests and checks

- `scripts/build_site.py`: the `parts` list; copy `site/player.js`.
  `tests/test_build_site.py`: `parts` per work (channels unique, one realization part in all 17 works, labels non-empty, including the five staves without an MEI
  label).
- `scripts/check_site.py` (Playwright, headless Chromium): press Play on Op. I/1, wait 2 s, require
  ≥ 1 `.is-playing` note and an advancing position; pin a measure on page 3, press Play and require the page
  label and `#player-position` to follow; change the tempo while playing and require the position to
  continue from the same measure with no MIDI re-render and to advance at the new rate; mute the
  realization channel and check the player state. Headless Chromium runs Web Audio without an output
  device; no sound check, only state.
- Manual check in the user's Brave and on an iPhone (Safari's silent switch and autoplay rules).
- CI unchanged apart from the extended `check_site.py` if it already runs there (it does not today: run
  it locally before each push of viewer changes).

## 6. Limitations to state in the viewer

- Op. II/2's and II/3's repeats play once until they get an explicit `<expansion>` (section 1); App. I's play.
- One tempo for the whole work: an Adagio and the Allegro after it play at the same quarter-note speed;
  the tempo words are printed but not interpreted. A tempo map from the words would be an editorial
  invention and stays out.
- The figured-bass figures do not sound by themselves; the continuo plays the bass line, and the
  realization is Stiehl's 1903 right and left hand.
- General MIDI samples, not period instruments; no ornaments beyond what the MEI encodes as notes.
- Each sample note lasts 3.13 s, so a longer violin, gamba or violone note stops short: 5 of the 48,066
  such notes at 100 % tempo, 36 at 75 %, 192 at 50 % (measured 2026-11-01).
- Play from a measure, or after Pause, starts every note held across the start point again from its
  attack: smplr 1.1.0 has no per-note sample offset. 696 of 3,568 measure starts (19.5 %) have such a
  note (Verovio MIDI, ties merged; measured 2026-11-01). A restarted harpsichord note also restarts its
  decay. Kept by the editor 2026-11-01 over dropping held notes (Codex and Cursor agreed).

## 7. Decisions

Second opinions (Codex and Cursor, `delegate ask --agent both`, 2026-11-01) agreed on all four
questions below, and the editor chose as they did (2026-11-01). Questions and answers:
`validation/runs/midi-player-plan/` (git-ignored).

| question | both picked | risks they raised (to build in) |
| --- | --- | --- |
| Tempo control | **percentage slider** (25–200 %, default 100 %) of the encoded tempo or of Verovio's ♩ = 120; one value, remembered; maps to `Transport.bpm` (4.1; `midiTempoAdjustment` only as fallback); same control in all three viewers | say beside the slider what 100 % means (♩ = 120, not the Allegro or Adagio of the print); compound meters (6/8, 12/8) and 3/2 still run on a quarter-note clock; 100 % keeps Webern I's encoding error, which needs its own fix |
| Start point and follow | **Play from the pinned measure**, else the first measure of the page on show, else the start; notes coloured, the playing measure's zone outlined on the scan, score and facsimile turn with the music; a manual turn or click stops following until the next Play; a click still pins | keep the playback cursor separate from the pin (calling `pin()` per measure would overwrite the start point and the URL hash); re-apply highlights after each page replacement; scan loading must never hold up the audio clock |
| Part switches | **one checkbox per part** in a small Parts menu, MEI labels plus "Realization (Stiehl)", all on by default, remembered by role across works | the realization's two staves are one part, so one checkbox; store the role, never the channel (channels follow score order and differ between works, e.g. App. II); show remembered "off" states clearly and offer "all on". `docs/mei-encoding-profile.md` already promises that a player can mute either continuo or realization |
| Where the code lives | **one self-contained `site/player.js`**, copied identically into each repo, wired from `viewer.js` | `build_site.py` copies an explicit file list (add `player.js` in every port); no edition constants inside the module; document its interface; stop playback and clear pending work before a work switch |

Player stack and sample hosting (section 3), asked 2026-11-01 after the research run; the agents split, and the editor chose A and the pinned
jsDelivr files:

| question | Codex | Cursor | risks they raised (to build in) |
| --- | --- | --- | --- |
| Player stack | **C**, js-synthesizer with a self-hosted SF2 extract: real loops, so no note stops short at any tempo | **A**, Tone.js + @tonejs/midi + smplr: the only no-build stack with a gain per channel for mute, a live `Transport.bpm` and Transport seek, all as pinned jsDelivr files | C: a mute must silence notes already sounding, not only drop new note-ons; an extract without GM 0 does not serve Webern, so the SoundFont must be configurable. A: the 3.13 s cut (5 notes at 100 %); drive the highlighting from the clock that drives the audio, or score and sound drift |
| Sample hosting (A, B) | **self-host** in each repository: the edition controls the bytes and their continued publication | **jsDelivr pinned** to Gleitzman's commit `044fab8e` with SRI, like Verovio; no 10.4 MB copy per repository | self-host: `build_site.py` copies an explicit file list, so the samples need their own copy step. jsDelivr: override smplr's default base URL (gleitz.github.io). Both: credit CC BY 3.0 (Gleitzman) and MIT (Wen), even when nothing is copied |

## 8. Implementation steps (one session each)

1. **Player module and wiring in this viewer** (stack A, section 3; delegate build from this plan as the spec): `site/player.js`,
   `viewer.js` wiring, CSS, the footer credit, `build_site.py` parts, tests, `check_site.py` checks. Gates: tests, review
   gate, `check_site.py`, a cross-vendor review, the user's listening check in Brave. Hand off after the
   review, before docs.
2. **Docs and release notes** (README viewer section and licence line, CHANGELOG Unreleased/Added), push,
   Pages check on the live site.
3. **Port to webern_op27.** Prerequisite: movement I's `scoreDef/@midi.bpm="40"` makes Verovio play
   ♩ = 40, but the print's mark is dotted ♪ = 40, which is ♩ = 30 (movement I plays a third too fast:
   60.7 s instead of ~81 s); fix the data in webern's own MIDI step first. II (♩ = 160) and III
   (half = 80, played ♩ = 160) agree with their marks. Piano only: no part switches.
4. **Port to DdT 1, vols. 29/30.** Prerequisite: every part there still has `midi.instrnum="0"` (piano;
   Pisendel 40 `instrDef`s, Hasse 6) and no tempo values; port `scripts/normalize_midi_data.py` with that
   edition's staff roles and decide its instruments first (own session, editor's decision).
