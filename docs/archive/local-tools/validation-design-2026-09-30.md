# Historical validation design — 2026-09-30

This preserves the original assessment. Missing-feature statements describe that date. See [the tool guide](../../../validation/README.md) for implemented behavior.

Implementation update, 2026-10-01: the entry point is now
[`scripts/validate_corpus.py`](../../../scripts/validate_corpus.py), with
[`validation/README.md`](../../../validation/README.md), a local profile and explicit
pilot work list. It uses the installed/local CAMAT implementation and records
version, commit, source hashes and execution statuses rather than permanently
pinning CAMAT during development. The assessment below is historical; the MEI
schema and score content were not changed by validator implementation.

# Validation responsibilities: CAMAT and DdT 1, volume 11

Assessment updated 2026-09-30 against the current CAMAT notebook and package implementation. Proposed interfaces and repository paths below are implementation targets, not delivered validators. This documentation update does not change CAMAT code, its notebook, or the musical text.

## Recommended architecture

Keep one shared validation engine in CAMAT. Give this repository a small command-line entry point that invokes that engine with the pinned schema, then runs this edition's metadata, source, and release rules. Keep the official MEI schema unchanged; the edition profile is an additional policy layer, not a fork of MEI CMN.

There are three distinct results:

1. **MEI conformance:** XML, RELAX NG, Schematron, and reference integrity for the declared schema and document context.
2. **Consumer and musical diagnostics:** things CAMAT or Verovio cannot handle, and likely musical inconsistencies requiring inspection. These do not automatically establish invalid MEI.
3. **Edition acceptance:** whether a file meets this repository's documented editorial and publication requirements.

Implement reusable mechanisms once in CAMAT; select required fields, allowed conventions, severity, and release scope in the repository. A small options object and repository Python rules are sufficient initially. An elaborate plugin framework or separate validation notebook is unnecessary.

The existing notebooks in this edition repository are earlier development artifacts and are not part of the planned workflow. CAMAT's notebook remains an optional interactive interface. The edition's release checks must also work without Jupyter.

## What the current implementation actually does

The CAMAT notebook imports package functions; `run_editorial_checks` combines the general checker, RELAX NG, figured-bass and page-break helpers, optional image-link checks, and Verovio. This package-based structure is useful and should be retained.

However, several rules already embed assumptions from this edition:

- `MeiChecker._check_publication_profile` expects BuxWV, BSB-ID, URN, an IIIF manifest, and the application names musiconn.scoresearch, Verovio, and mei-friend. Those are not universal publication requirements. Software provenance must describe tools actually used.
- `_check_facsimile_zones` warns about missing measure zones even when `publication_profile=False`. A score without facsimiles is valid MEI.
- `_check_facsimile_page_structure` expects one graphic per surface, numeric page labels, and IIIF canvas links. These are profile or consumer conventions. MEI permits multiple graphics, including different resolutions, on a surface.
- `iiif_graphic_target_rows` treats ordinary image paths and non-IIIF image URLs as warnings. The viewer's `resolve_graphic_src` already supports local relative images and ordinary HTTP image targets.
- `figured_bass_report_rows` warns when valid `harm/@startid` can be converted to `tstamp`. A preference for one anchoring style belongs to a selected profile. Missing targets and invalid anchoring are different issues.
- The reference checker omits `resp` and `source`. A bare fragment absent locally can also be downgraded to information if its ID occurs in another selected file; that should be an explicit page-assembly mode, not standalone-file validation.
- RELAX NG is executed, but the embedded Schematron is not. A declaration requesting Schematron is not evidence that it ran.

Two temporary probes on 2026-09-30 confirmed the facsimile distinction: removing facsimiles and all `@facs` attributes from the pilot remained RELAX NG-valid but produced 183 `measure_facs` findings in general mode. Adding a second graphic to one surface also remained RELAX NG-valid but produced a `surface_graphic_count` error in publication mode. These are focused RELAX NG/checker comparisons, not complete validation of those hypothetical variants. The real score was unchanged.

Relevant implementation: `camat/check_mei_consistency.py`, `camat/mei_consistency_workflow.py`, `camat/facsimile_viewer.py`, and `tests/test_mei_consistency.py` in the CAMAT repository. The official [facsimile guidelines](https://music-encoding.org/guidelines/v5/MEI_Guidelines_v5.1.pdf) show multiple graphics and ordinary image targets.

## Shared checks to implement or retain in CAMAT

### Schema and execution infrastructure

- Parse XML and check the MEI namespace, duplicate IDs, and declared version/customization.
- Run RELAX NG and genuine Schematron against a configured, pinned schema. MEI 5.1 CMN can remain the default; another explicitly selected schema is not an edition error merely because it differs from that default. Report unsupported schemas or validator dependencies explicitly.
- Compare parsed `xml-model` declarations with the selected schema/version when declarations are supplied. Requiring both declarations is a publication-profile decision. Avoid substring tests that accept the same schema basename under a wrong release URL.
- Preserve structured findings with stable rule IDs, file, line, element ID, measure/staff context, severity, and rule origin. Keep execution status separate from findings.
- Make checking read-only. Expose cleanup and conversion as explicit transformation operations with their own outputs and reviewable differences.

A proposed `run_schematron_validation` should preserve embedded namespaces, execute XPath 2 expressions, and retain or parse SVRL. Use a pinned compatible compiler and processor; lxml's XPath 1 Schematron route is not sufficient for these rules. Cache compiled validators by schema hash and compiler version. Compilation failure, missing dependencies, or extraction of zero rules must never become a pass. The earlier pilot assessment successfully executed the embedded rules; that implementation still needs to enter CAMAT.

### IDs, references, and reusable profile helpers

- Share a schema-aware URI-reference registry between validation and ID-rewriting code. Cover `resp` and `source` as well as existing linkage attributes, handling lists, relative document URIs, fragments, and applicable base URIs. Do not treat every MEI attribute as a pointer.
- In normal standalone mode, a bare `#id` must resolve in its own document. Retain cross-page assembly diagnostics under an explicit option. Explicit references such as `other.mei#id` need bundle-aware resolution when the bundle is available.
- Check target types according to the chosen MEI schema. A general responsibility check must not require every `@resp` to point specifically to `respStmt`; this repository can adopt that narrower convention.
- Provide an optional addressability check accepting a configured set of elements that require IDs. The MEI schema's optional IDs are not all mandatory by default; this edition deliberately requires a larger event set for annotation and analysis.
- Provide scoped metadata helpers, such as checking `fileDesc/pubStmt/availability`. The mechanism is reusable; requiring a particular publisher, license, identifier type, or editorial category belongs to the chosen profile.

### Musical and consumer diagnostics

Retain checks for duration consistency, staff/layer references, pitch attributes, spans, and figured-bass anchors where their semantics are supported. Classify rhythm heuristics as CMN diagnostics and account for pickups, `metcon`, tuplets, grace notes, meter changes, and editorial alternatives. Do not sum both branches of `choice` or `app`; specify the reading or report that a timing check is unsupported. Measure numbering, omitted staves, and single-layer numbering can be legitimate editorial choices.

Compare written durations and optional `dur.ppq` as a diagnostic. A ban on PPQ attributes, or a decision that written duration overrides performance timing, is an edition policy. Likewise, `accid.ges` may carry intentional sounding-pitch information; its presence is not automatically import noise.

Keep Verovio loading/rendering distinct from CAMAT parsing and playback expansion. Add an optional CAMAT consumer probe using the backend and interpretation intended for release: parser exceptions, event identity, staff mapping, and representative pitch/duration behavior. Do not require raw XML note count to equal parsed rows universally; ties, repetitions, alternatives, and selected views affect that relationship.

### Facsimile mechanisms

When facsimile data is supplied, check reference integrity, geometry, image metadata, and optionally resource accessibility. Handle local files, direct HTTP images, and IIIF separately. Recognize IIIF from its declared service/request structure where available, not merely a `/iiif/` substring. A relative path is not a failed HTTP request.

Evaluate zones in the declared surface coordinate space, then check their mapping to the selected graphic. Do not assume surface coordinates always equal the first graphic's pixel dimensions, particularly with multiple image resolutions. Check image existence and decoding offline where possible; online reachability is a separate optional pass. No facsimile, multiple graphics, nonnumeric printed page labels, and no IIIF manifest should not by themselves fail general MEI validation.

## Rules owned by this edition repository

The repository validator selects and enforces these rules from the [encoding profile](../../mei-encoding-profile.md) and [editorial policy](../../editorial-policy.md):

- Exact MEI 5.1 CMN declarations, pinned schema hash, required header paths, separate digital-data and image rights, and the edition's responsibility convention.
- Stable local edition key, work/BuxWV identity, `mdiv` work linkage, working/final filename mapping, release version/date/URI agreement, and explicit inclusion of release-ready works. Do not validate page-level OMR inputs as final editions.
- DdT's BSB record, URN, manifest, source-page mapping, and bibliographic identity. Require the appropriate Uppsala witness when used: B5204 for Op. I, B5205 for Op. II. Appendix sources must be reviewed individually; neither this mapping nor the pilot's five-staff arrangement applies automatically to all appendix works.
- Complete IDs for the edition's addressable events and controls, plus locally resolved fragments in every standalone published file.
- Source-faithful page/system breaks and measure-zone coverage for the **primary DdT facsimile**. Keep work-local surface numbering separate from printed page labels. If the profile chooses one access graphic per primary surface, label that as a house convention.
- Editorial annotation categories, affected-event links, responsible editor, source reading, encoded reading, and stated rationale/evidence. An automatic check can establish their presence, not verify that the musical argument is sound.
- Per-work staff roles and treatment of the DdT keyboard realization. Preserve the master score; explicitly identify any analytical selection. The first three staves are a pilot-specific view, not a universal original-print reconstruction.
- Scan inventory, derivative/master mapping and hashes, documented image terms, and reproducible derivative settings. Supplementary witnesses need usable source/part/page citations; they do not need a second complete measure-zone layer or a competing `pb` sequence.
- Corpus-level uniqueness, manifest coverage, documented exceptions, citation metadata, and release evidence.

Unknown Uppsala redistribution terms prevent marking those images ready for public distribution. They do not make a bibliographically documented witness invalid or automatically block an MEI-only release. Require the actual terms for any image files included in the release.

## Repository entry point and reporting

Proposed repository artifacts are `validation/profile.json`, `validation/rules.py`, `scripts/validate_corpus.py`, a work manifest, and focused validator fixtures. These names are provisional. The profile records constants/options; Python rules handle cross-document and corpus-specific relationships. Additional repository Schematron can be added later if it makes header constraints easier to maintain; duplicating every rule in Python and Schematron is unnecessary.

The entry point should load the explicit work list, invoke a pinned CAMAT version and the local schema, append edition findings, write reports, and return a failing exit status when required checks fail. Provide review and release modes: review accepts working filenames and incomplete editorial status while reporting outstanding work; release enforces final naming, completed review, manifest consistency, and required pass execution.

Use a findings file plus a run record containing input hashes, profile/schema hashes, tool versions, requested checks, actual statuses, and reviewed exceptions. Suggested statuses are `passed`, `failed`, `skipped`, and `execution-error`. A required skipped check blocks release. Keep rule severity separate from whether the validator ran. Exceptions identify the rule, work/event, reason, reviewer/date, and input revision; a changed affected passage requires renewed review.

Fast offline checks should run during editing and in CI. Full rendering and CAMAT parsing can run for release candidates. Network checks should be an explicit connectivity report: an unavailable external image server does not establish invalid MEI. Reuse the same entry point in CI and locally.

## Notebook adjustments

The inspected notebook has `CHECK_PUBLICATION_PROFILE`, `CHECK_RELAXNG`, `CHECK_PPQ`, `CHECK_FB_TSTAMP`, `CHECK_PB_FACS`, and full Verovio rendering enabled; image-link checks and `RUN_PIPELINE` are disabled. Its active input/output paths refer to the Pisendel concerto in DdT volumes 29/30, while introductory prose still names Buxtehude.

Replace the ambiguous publication boolean with an explicit selected profile or equivalent options. General CAMAT mode should not silently select this edition's rules. Separate schema checks, musical diagnostics, optional consumer checks, and optional facsimile conventions in the configuration. Add Schematron execution and a visible run-status summary. Keep notebook cells as orchestration and display, with tested functions in CAMAT.

Correct the stale example prose and the claim that checking always leaves inputs untouched: in check-only mode, enabled `STRIP_PPQ` or `STRIP_ACCID_GES` currently invokes cleanup on the original files. Until that separation is implemented, keep both false. Avoid running the base checker twice when the combined check already invokes it; the current check-only branch does this.

## Acceptance cases for implementation

Shared CAMAT tests should cover schema/Schematron failures, a deliberately failing Schematron-only assertion, namespace-preserving extraction, unavailable validators, duplicate/broken IDs, `resp`/`source` handling, standalone versus assembly references, and pointer preservation after ID rewriting. Positive cases must include valid MEI without facsimiles, local/direct image targets, multiple graphics, and valid `harm/@startid` without a style warning in general mode. Add representative timing/alternative cases before broadening musical assertions.

Repository tests should cover a digital license missing while an image license remains, wrong schema-version declarations, wrong opus/source mapping, missing release-event IDs, incomplete annotations, mismatched final URI/filename/version, a missing manifest work, and a broken local derivative link. Include valid conjectural emendations, appendix-specific source/role mappings, and bibliographic witnesses without public scans. Test that a disabled required pass and an empty finding list cannot together yield a release pass.

The ordered implementation and facsimile preparation plan is in the [archived plan](../planning/finalization-plan-2026-10-01.md).
