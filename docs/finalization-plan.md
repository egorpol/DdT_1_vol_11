# Dataset finalization plan

Prepared 2026-09-30; implementation status updated 2026-10-01. The general
CAMAT engine and this repository's dedicated script/notebook are implemented for
the explicit Op. I/1 pilot work list. Local update/viewer-sync helpers and an
inspected legacy-tool archive are also available. Each run records the actual
CAMAT installation/revision/source hashes; no permanent development pin or new
release is declared. See [the tool guide](../validation/README.md) and
[validation responsibilities](validation-workflow.md) for current behavior.

The numbered steps below remain the broader finalization plan. The pilot is
still under review. Its source entries, event IDs and annotation metadata have
been completed, and local scan derivatives have conversion inventories. Official
IIIF warnings, image redistribution, complete release coverage and publication
sign-off remain outstanding. The [pilot baseline](../validation/pilot-baseline.json)
records the tested input and actual CAMAT state. The [encoding profile](mei-encoding-profile.md) and
[editorial policy](editorial-policy.md) define the intended outcome.

The Uppsala witnesses discussed here are Op. I, Lübeck **[1696]**, RISM A/I B5204, and Op. II, Lübeck **1696**, B5205, both catalogued as S-Uu, Uimtr 52:1–4. The later reference to “1689” is treated as a typo; it is not adopted as a source date. Verify the physical items and partbook arrangement during inventory rather than inferring their number from the shelfmark range. See the [library's printed-music catalogue](https://www2.musik.uu.se/duben/Printed%20music%20in%20the%20Duben%20Collection2024.pdf).

## 1. Define the validation boundary and preserve a baseline

**Work in both repositories.** Record the pilot's current checksum and the CAMAT revision. Use this corrected sonata as the main integration example, plus a small ordinary MEI without facsimiles and a score from another composer to guard against accidental Buxtehude requirements.

Agree the three result categories: MEI conformance, consumer/musical diagnostics, and DdT publication acceptance. Keep the existing official MEI 5.1 CMN schema. List each current rule's owner using the validation document; include rules currently active outside the publication flag.

The local edition notebooks are legacy development artifacts. Before removing them, check for any unique editorial decisions or transformations that have not reached CAMAT or the docs. Do not make their continued presence a dependency of the new validator. The duplicated generic script in this repository should be retired or replaced by a small compatibility wrapper once CAMAT supplies its needed behavior.

**Complete when:** the rule boundary and release input list are explicit, and the baseline is reproducible. This step does not require a complete new manifest system.

## 2. Improve the shared CAMAT checks

**Work in CAMAT.** First separate edition assumptions and mutating cleanup from general checking. Keep CMN as the configured default, while making schema/profile choices explicit. Then add real Schematron execution, shared reference handling, standalone/assembly modes, generalized image-resource checks, and execution records. Add consumer parsing as an optional pass.

The notebook remains a thin interface to these functions. Correct its stale example description and make the active profile, paths, and executed/skipped checks visible. Expose conversion commands separately so a validation run cannot silently rewrite input MEI.

Add regression cases for the observed gaps and valid counterexamples listed in the validation document. Retain existing public entry points or provide a documented migration route for their callers. Record changes in CAMAT's release notes.

**Complete when:** valid scores without BuxWV or facsimiles pass general mode; broken pointers and a Schematron-only violation fail; missing validators cannot produce a pass; checks leave input hashes unchanged. Publish or pin the tested CAMAT revision for use by this corpus.

## 3. Add the repository's validation entry point

**Work here.** Implement the small profile, edition rules, and command-line wrapper described in the validation document. Reuse CAMAT's schema, pointer, diagnostic, rendering, and reporting mechanisms. Keep bibliography, required fields, source/opus mappings, filename conventions, editorial categories, and release acceptance here.

Start a work manifest with stable edition keys, current paths, work identity, editorial status, source IDs, and staff roles. The manifest must distinguish included release works from incomplete works; the existence of a combined file does not establish finalization. Define a separate image inventory linked to source IDs, avoiding duplication of source images across sonatas.

Provide review mode for `_corr` files and release mode for final filenames and metadata. Initially add a few deliberate failures: wrong source/opus, missing digital license, incomplete annotation, and a broken image path. Check that the pilot's known encoding comments and conjectures are handled appropriately.

**Complete when:** one documented command produces both CAMAT and edition findings, with a machine-readable execution record, without Jupyter. Tests demonstrate both acceptance and rejection. A release run cannot quietly omit required checks.

## 4. Inventory the 1696 scans and choose an access derivative

**Editorial preparation can begin alongside steps 1–3.** Confirm redistribution and attribution terms with the library, including permission for converted/resized copies, and retain the written response. Source descriptions and private inspection can proceed while publication terms are being clarified.

Inventory the actual TIFFs: original filename, source/opus, physical volume or partbook, printed part label, scan sequence, printed page or folio label, TIFF frame count, pixel dimensions, bit depth, orientation, compression, ICC metadata, file size, and SHA-256. Preserve covers, title pages, blanks, and irregular numbering in the inventory. Do not assume one TIFF equals one page or that scanner settings fully describe every delivered file.

Choose three representative images: dense music with small figures/dots, a faint or damaged page, and a title page or spread. Produce trial JPEGs using the recipe below. Inspect them against the TIFFs at native pixel scale and at the viewer's intended zoom. Measure actual page and total estimated sizes before choosing storage. Check accidentals, small figured-bass numerals, augmentation dots, ties, staff lines, and marginal marks.

**Complete when:** master files are preserved and inventoried, one conversion recipe is approved on real images, and image publication terms are known before public distribution. The current assessment inspected the supplied scanner settings, not the TIFF files, so it cannot certify resolution, fidelity, or expected compression ratio.

## 5. Prepare and link the facsimiles

**Work here and in the chosen image storage.** Convert the remaining access images using the tested recipe; retain a log, software version, input/output hashes, and page mapping. Use stable source and partbook identifiers rather than temporary scanner filenames. A proposed relative layout is `facsimiles/uppsala/op1/<partbook-id>/0001.jpg` and the corresponding `op2` layout. The partbook IDs must come from the actual inventory.

Keep an image inventory and source-specific rights/readme file alongside the access images. Record original filename/hash, derivative path/hash/dimensions, printed label, transformations, and any omitted or missing scans. A checksum for a privately held master provides fixity, not public access; describe its storage/access status honestly. Publish only the permitted image assets and suitable provenance metadata.

Retain the DdT/BSB score as the primary facsimile alignment. Link the Uppsala images as supplementary witnesses with source/part/page locators; add detailed zones only where they support collation. Do not replace the existing DdT surfaces or apply DdT measure coordinates to original partbooks. Test source selection before adding supplementary surfaces to the same viewer model.

Use relative image targets for a downloadable bundle, resolved from each MEI file's location, or stable direct image URLs for remote access. Verify that the released directory layout preserves those references. A local checkout working does not prove a remotely opened MEI can find the same images. A per-partbook PDF can be an optional reading download; individual image files remain the simplest inputs for page/zone addressing.

**Complete when:** the pilot's cited original-source passages are locatable, images render locally and in the intended distribution mode, rights are explicit, and no existing DdT alignment has changed inadvertently.

## 6. Finalize one sonata end to end

**Editorial work here.** Apply the revised header to Op. I/1: source identities, responsibilities, actual software provenance, working edition metadata, and editorial declaration. Preserve the repaired event IDs.

Review every substantive departure from DdT. Classify source-supported and conjectural emendations, record source and encoded readings, and cite actual part/page evidence. In particular, the original print's lack of a keyboard realization cannot support a specific rhythmic correction to DdT's realization; that needs its own musical rationale. Separate encoding explanations from changes to the musical reading.

Declare analytical staff roles while keeping the five-staff master as printed. Decide the default CAMAT analysis view explicitly, so inclusion of the keyboard realization is intentional. Check rendering and parsing under that interpretation. Have a human reviewer compare the corrected musical text, annotations, and facsimiles; automated checks do not replace that review.

**Complete when:** the pilot meets review-mode requirements, outstanding readings and accepted tool limitations are documented, and its editorial review is recorded. Promote the working profile to version 1 only after this end-to-end trial is stable.

## 7. Apply the workflow to the remaining works

**Editorial work here.** Work through the corpus by actual status: assemble missing works, correct musical content, migrate headers, review source evidence, declare staff roles, then validate. Do not infer that other sonatas pass because the pilot does. Review the three appendix works' sources, instrumentation, and editorial treatment individually.

Update the manifest and public status together. Automate repetitive metadata changes only after checking the resulting diff on a small batch. Preserve event IDs and add truthful revision entries. Resolve each finding or record a specific reviewed exception; do not erase intentional source anomalies to make reports empty.

**Complete when:** every work selected for release has complete metadata, reviewed music and interventions, source access information, and a successful validation record for its actual bytes. Document any deferred works explicitly.

## 8. Create the release and its validation record

**Publication preparation here.** Set the real release version/date, final filenames and corresponding URIs together. Validate the final renamed files again, then generate their checksums and release manifest. Keep the MEI-data license, BSB image terms, and Uppsala image terms separate in both headers and repository documentation.

Add citation metadata, release notes, the profile version, validation record, known limitations, and instructions for selecting analytical views and locating facsimiles. Tag and archive the actual release; add a DOI or other archive identifier only once assigned. Verify that final public URLs and downloadable bundle references work. Keep any offline validation rerunnable from pinned software and the archived schema/profile.

**Complete when:** a fresh user can identify the edition and sources, reproduce the required checks, access the permitted images, understand interventions, and cite an immutable release.

## Recommended image formats and storage

**Preservation:** retain the delivered TIFFs unchanged as received, with hashes and backups, outside normal Git history. TIFF is a well-established master format; the [Library of Congress TIFF description](https://www.loc.gov/preservation/digital/formats/fdd/fdd000022.shtml) documents that use. If storage savings are necessary, test lossless LZW or Deflate TIFF copies and verify decoded pixels, page count, orientation, and important metadata. Preserve the original delivered files; compression changes file hashes even when decoded pixels match.

**Repository access copy:** start with JPEG at quality 95, full original pixel dimensions, and 4:4:4 sampling, using a pinned encoder. Compare quality 90 if the batch is too large. These are trial settings, not a universal quality standard; quality scales vary by encoder. Keep colour, avoid sharpening/denoising/thresholding, and encode each derivative from the master rather than from an earlier JPEG. Prefer lossless PNG for an exceptional page if JPEG artifacts obscure evidence. WebP can be an optional optimized derivative later; adding another required format is unnecessary for the first release. JPEG has broad browser support, while TIFF support is limited; see [MDN's image format guide](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Image_types).

The supplied settings indicate `fileformat=tiff`, `tiff_compr=none`, `dpi=300`, and `colormode=truecolor`. Uncompressed colour pixels explain large files. `jpeg_quality=75` is a separate setting and does not show that these TIFFs contain JPEG-compressed data. Inspect actual TIFF tags to confirm compression, dimensions and bit depth. Changing only the DPI metadata does not reduce pixel count or file size.

Start without resizing. If needed after visual review, test a maximum long edge of approximately 4000 pixels alongside full resolution, never upscaling. Thin notation and small numerals determine the acceptable result; no fixed pixel target guarantees legibility. Freeze orientation, cropping, page splitting, and output size before drawing new zones. If derivatives subsequently change size or geometry, update and verify the coordinate mapping. Preserve the original spread and record mappings if page splitting is introduced.

The settings also say `colorspace=native`, `cms=off`, and `profile=off`. Inspect actual embedded ICC data. Convert to sRGB using a known source profile when available; otherwise document the uncharacterized colour and any explicit display assumption. Do not invent a scanner profile or claim calibrated colour. Keep any bit-depth conversion confined to access copies and record it.

**Storage decision:** keep the image inventory, rights information, recipe, and checksums in the corpus repository. A modest, mostly immutable JPEG set can also live there. If the measured derivative set substantially enlarges normal clones, use separately hosted static images for browsing and a versioned image bundle/archive for download. Git LFS is an option if LFS-aware distribution is deliberately supported, but it is not an archival strategy or an IIIF service. Verify actual download/viewer behavior before choosing it.

GitHub warns for files over 50 MiB and blocks files over 100 MiB in ordinary Git; it recommends repositories ideally below 1 GB. These are hosting constraints, not image-quality targets, and keeping each file below 100 MiB does not make a multi-gigabyte scan collection a good fit for Git. See [GitHub's large-file guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

MEI does not require IIIF: `graphic/@target` can identify an ordinary image resource. The current CAMAT viewer resolves local relative files into displayable image sources. Its current IIIF-specific validator needs the generalization in step 2. For many pages, test viewer load/memory behavior because embedding images into HTML adds overhead. A future IIIF service or static Presentation manifest is optional infrastructure; it is not a prerequisite for this edition's first release. See the [MEI graphic definition](https://music-encoding.org/guidelines/v5/elements/graphic.html).
