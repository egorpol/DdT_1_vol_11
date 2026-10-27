# Release 1.0 checklist

Status 2026-10-27: all 17 works are corrected working files (`_corr` filenames). They are not finalized. The 0.10.0 pre-release contains all 17 (0.9.0 contained the earlier 16).

The validation boundary, the shared CAMAT checks and this corpus's validator are in place (steps 1–3 of the [archived plan](archive/planning/finalization-plan-2026-10-01.md), with CAMAT 0.2.7). The items below are what remains before a 1.0 release. The [tool guide](../validation/README.md) describes the checks, the [encoding profile](mei-encoding-profile.md) the target header and the [editorial policy](editorial-policy.md) the intervention categories.

## Scope

- [ ] Decide whether 1.0 contains the earlier 16 works or all 17 corrected works, including Op. II/1.
- [ ] List every released work in `validation/works.json` with its own identities, consulted sources, page range and staff roles. Today the publication work list holds Op. I/1 only; nothing is copied from the pilot to other works.

## Editorial review, per work

- [ ] Review every substantive departure from DdT and classify it as an OMR repair, a source-supported or conjectural emendation, or an encoding note, citing part and page evidence. The lack of a keyboard realization in the original prints cannot by itself justify a rhythmic correction to DdT's realization.
- [ ] Resolve or explicitly retain the interim conjecture in App. II, m. 156.
- [ ] Review the three appendix works' sources, instrumentation and editorial treatment individually.
- [ ] Decide how the official Schematron warnings on external IIIF canvas `surface/@corresp` values are treated. Release mode blocks unresolved warnings, and no waiver is configured.
- [ ] Have a named reviewer compare the encoded music, the annotations and the facsimile, and record the hash-bound sign-off that release mode requires. An empty report does not replace this review.

## Facsimiles and rights

- [ ] Keep the MEI-data licence, the BSB image terms and any Uppsala image terms separate in the headers and the documentation.
- [ ] Uppsala witnesses (STIMU 1991 reproductions): obtain the reuse terms for the scans and their derivatives before publishing any image. See the [scan guide](uppsala-facsimiles.md). Until then the images stay local, and the MEI cites the witnesses by source, part and page.
- [ ] If images are cleared: inspect and record printed page labels in the inventories, decide on the mixed scan 4 (crop the historical title page or omit the spread), and choose the image storage (repository, separate hosting or a versioned bundle; see the archived plan's storage section).
- [ ] The DdT/BSB surfaces remain the primary alignment. Supplementary Uppsala surfaces must not change existing DdT zones.

## Files and metadata

- [x] Encode an explicit first-page title and composer heading in all 17 scores, retaining the authority-linked composer metadata and supporting standalone exports (2026-10-26).
- [ ] Remove the `_corr` suffix and set the final filenames and publication URIs together, following the `altId[@type='repository-stem']` mapping in the [editorial workflow](editorial-workflow.md#file-naming).
- [ ] Set one edition version and release date in every header, with a revision entry for the release. Release mode reads the first `pubStmt/date` as the release date; the current first dates record working-edition updates, so replace them with the actual release date when preparing publication.
- [ ] Rerun the full editorial report set on the final filenames and commit its provenance.

## Release gate and archive

- [x] Make the release-mode check compare each selected file's bytes with the blob at the declared immutable commit and at the release tag that the versioned URI names, not only confirm that the commit exists.
- [ ] `python scripts/validate_corpus.py --mode release` accepts every released work: final file, URI and versioned URI, release version and date, immutable commit and local release tag, current input hashes, persistent event IDs, sign-off and `CITATION.cff`.
- [ ] Release notes with the profile version, the validation record, known limitations, and instructions for choosing analytical views and locating facsimiles.
- [ ] Push the release tag (created locally before the release-mode run), archive it with a persistent identifier (DOI), and add the identifier to the citation metadata once it is assigned.
- [ ] From a fresh clone, verify the public URLs, the image references and that the checks can be rerun with the pinned CAMAT version.

**Complete when:** a new user can identify the edition and its sources, rerun the required checks, open the permitted images, see every intervention and cite an immutable release.
