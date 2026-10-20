# Validation workflow and responsibility boundary

## Current implementation — 2026-10-01

Use [`scripts/validate_corpus.py`](../scripts/validate_corpus.py) or
[`mei_corpus_checks.ipynb`](../mei_corpus_checks.ipynb). Both call the installed
CAMAT general validator, then apply this repository's explicit policy and work
list. Neither installs/updates dependencies nor rewrites the selected MEI during
checking. The [tool guide](../validation/README.md) contains commands, reports,
version tracking and review/release semantics.

The publication work list selects only Op. I/1. Other files are inventoried as
unlisted, not implicitly validated or accepted for publication. Expand the list
with reviewed per-work identities, source mappings and staff roles. BuxWV, Uppsala
opus witnesses and the pilot's five-staff arrangement are local selections.

## Known issues in the original OMR pages

The preserved page-level OMR contains duplicate `xml:id` values in four files:

- [BSB image 00023](../11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/bsb00023199_00023_facs_zones.mei): `d2qjhlp`, `i1p4r9x5`, `l4i9dkd`, `p1a251yb`.
- [BSB image 00028](../11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/bsb00023199_00028_facs_zones.mei): `z1n4bkpv`.
- [BSB image 00049](../11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/bsb00023199_00049_facs_zones.mei): `r5xd43`.
- [BSB image 00090](../11_buxtehude_dietrich_buxtehudes_instrumentalwerke_bsb00023199/bsb00023199_00090_facs_zones.mei): `qkpviw6`.

These issues predate the 2026-10-01 push preparation; the four files retain their
previous committed bytes. Their IDs and affected references need review before
using them as validated standalone MEI or input to a new assembly. The corrected
Op. I/1 pilot is checked independently through the explicit work list.

## What CAMAT owns

- XML readability, unique IDs and supported local/bundle pointer resolution in
  explicit standalone/assembly contexts, including `resp`, `source`, URI lists,
  document fragments and `xml:base`; remote authority documents are not fetched.
- The configured unchanged official MEI 5.1 CMN RELAX NG and genuine embedded
  Schematron execution, including namespace preservation, XPath 2 rules, SVRL and
  missing-validator/incomplete execution handling. An XML schema declaration
  alone does not execute those passes.
- Offline supplied raster/SVG resources and declared coordinate bounds; optional
  HTTP image accessibility. Facsimiles, IIIF or numeric surface names are not
  general MEI requirements.
- Supported musical diagnostics and optional Verovio/CAMAT consumer probing,
  kept distinct from schema validity. Alternative readings and complex timing
  still need contextual review; consumer tables are not event-fidelity proof.
- Read-only orchestration, findings serialization, execution/provenance records
  and input hashes. Conversion, assembly and cleanup are separate explicit calls.

## What this corpus owns

`validation/profile.json`, `validation/works.json` and `validation/rules.py`
select exact schema declarations/hash, header paths and MEI-data license,
work/file/catalogue/source identity, responsibility convention, persistent event
IDs, per-work staff roles, primary facsimile surfaces/page numbering and
measure-zone/page relationships, and annotation fields/evidence/review.

Release additionally requires final filename and URI, release version/date,
locally verifiable immutable commit URL, recorded input hashes and human
sign-off. The supported release scope is MEI data only. Full image-redistribution
inventory, scan-derivative checks, system-band topology inference and complete
cross-work release coverage remain separate work, not implemented guarantees.

Official pilot warnings on external IIIF canvas `surface/@corresp` remain pending
publication review. Shared conformance retains their advisory severity; local
review reports the pending decision and release blocks unresolved warnings.
No exception or waiver is configured.

## Shared editorial reports

The tracked CSVs beside each assembled score are used by student contributors.
`scripts/refresh_editorial_reports.py` selects all 16 assembled scores through
the separate review-only `validation/editorial-works.json`, applies current CAMAT
and DdT checks to each score, and records portable provenance in
`validation/editorial-reports.json`. Work-specific configuration gaps remain
findings; the pilot's five-staff map and historical witnesses are not defaults.
Op. II/1 remains unassembled. The publication manifest and human sign-off process
are unchanged. Full run artifacts and previous report backups remain local.
See [the tool guide](../validation/README.md#refresh-the-reports-used-by-contributors).

## Reports and interfaces

Keep **MEI conformance**, **consumer diagnostics** and **DdT publication
acceptance** separate. Review can report `needs-review` with exit code zero;
release requires actual acceptance. Missing required validators, disabled
Schematron, empty input selection and policy execution errors cannot yield a pass.

Top-level CSV/JSON findings combine shared and local evidence; `origin` and
`check` distinguish it. `general/` preserves the CAMAT-only findings and SVRL.
`run.json` records the actual installation, schema/profile/work-list/code and
input hashes, both repository identities, requested/executed checks and acceptance.
Reuse replaces the current run; archive the full report folder for evidence.
Native hard timeouts are not yet implemented; incomplete progress remains visible.

Use [`scripts/update_camat.py`](../scripts/update_camat.py) separately to install
an editable local checkout or an explicit remote Git snapshot. Validation uses
that installed implementation, with no permanent development pin and no silent
pull. A PyPI update needs a published release; local/Git code does not.

Use [`scripts/sync_camat_viewer.py`](../scripts/sync_camat_viewer.py) to refresh
[`mei_facsimile_viewer.ipynb`](../mei_facsimile_viewer.ipynb) from CAMAT's local
notebook with corpus setup/input adaptation, configuration preservation and backups.

## Legacy artifacts

The [migration audit](archive/local-tools/README.md) records the inspected old
notebooks/scripts, retained operations and local recovery archive. The old
[validation design](archive/local-tools/validation-design-2026-09-30.md) remains
historical evidence. These artifacts are not validation dependencies.

For editorial requirements, see [the encoding profile](mei-encoding-profile.md)
and [editorial policy](editorial-policy.md). An automated report cannot establish
source-faithful pitch, rhythm, articulation, accidentals, figures or readings.
