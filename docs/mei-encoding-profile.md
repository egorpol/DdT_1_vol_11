# MEI Encoding and Publication Profile

This document records the technical publication profile for the complete sonata- and appendix-level MEI files in this repository. It is intended for editors, maintainers, and validators; the main README remains a public overview of the corpus.

The current pilot implementation is [`buxtehude_op1_01_sonata_f_major_corr.mei`](../11_buxtehude_sonatas_final/buxtehude_op1_01_sonata_f_major_corr.mei). A reusable skeleton is available as [`templates/mei-header-template.xml`](templates/mei-header-template.xml).

## Schema profile

Publication files use the official MEI 5.1 Common Music Notation customization:

```xml
<?xml-model href="https://music-encoding.org/schema/5.1/mei-CMN.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<?xml-model href="https://music-encoding.org/schema/5.1/mei-CMN.rng" type="application/xml" schematypens="http://purl.oclc.org/dsdl/schematron"?>
<mei xmlns="http://www.music-encoding.org/ns/mei" meiversion="5.1+CMN">
```

The XML model declarations and `mei/@meiversion` must identify the same MEI release and customization. The repository includes a pinned copy at [`schemas/mei-CMN-5.1.rng`](../schemas/mei-CMN-5.1.rng) for reproducible and offline validation. It is reference and validation infrastructure rather than edition content embedded in an MEI file.

## Header model

The header distinguishes the encoded file, the historical source, the encoding process, the abstract musical work, and the file's revision history.

| Section | Purpose |
| --- | --- |
| `fileDesc/titleStmt` | Work title, composer, and responsibility for the digital file |
| `fileDesc/editionStmt` | Release designation and semantic version |
| `fileDesc/pubStmt` | Digital publisher, release date, canonical URI, and MEI-data license |
| `fileDesc/sourceDesc` | Bibliographic description, identifiers, location, page range, facsimile links, and image license |
| `encodingDesc/appInfo` | Significant software stages in the creation of the encoding |
| `encodingDesc/editorialDecl` | Correction policy, interventions, and facsimile conventions |
| `encodingDesc/projectDesc` | Project and funding context |
| `workList/work` | Stable work identifier, catalogue number, title, composer, key, and performing medium |
| `revisionDesc` | Meaningful lifecycle events, newest first |

The structure follows the [MEI metadata guidelines](https://music-encoding.org/guidelines/v5/content/metadata.html). Keep the header concise: add `xml:id` only to entities that must be addressed by references such as `resp`, `decls`, or other pointers.

## Title and edition statement

Use the work title alone in `titleStmt/title`, for example:

```xml
<title>Sonata I in F major, Op. I</title>
```

The phrase “digital MEI edition” is edition information, not part of the displayed work title. Record it in `editionStmt`, for example:

```xml
<edition n="1.0.0">First digital edition</edition>
```

Verovio derives the first-page score heading from the metadata title. Add `pgHead` only when page-header content must be encoded explicitly; do not duplicate the title in both places merely to control display.

## Responsibilities and revisions

Separate modern digital responsibilities from the editorship of the 1903 source. Carl Stiehl belongs in `sourceDesc`; contributors responsible for assembly, correction, review, or metadata belong in `titleStmt/respStmt`.

Use `revisionDesc` for significant work-level events such as assembly, completion of correction, application of the publication profile, and release. Each `change/@resp` should point to the relevant `respStmt/@xml:id`. Dates and responsibilities must describe actual work and should be confirmed before publication.

## Source and licensing

The MEI data and the BSB facsimile are separate resources and require separate rights statements:

- Record the repository's MEI-data license in `pubStmt/availability`.
- Record the facsimile provider and image-use terms inside the bibliographic source description.
- Retain the BSB URN, local identifiers, holding institution, shelfmark, digital record, IIIF manifest, and printed page range.

## Work declarations

Each complete file declares one principal `work` with a stable `xml:id`. Its `mdiv/@decls` points to that work. For Buxtehude sonatas, record the BuxWV identifier, normalized title, key, composer authority record, and performing medium when known.

The repository stem is file-management information and is recorded separately as `meiHead/altId[@type='repository-stem']`; it is not a substitute for the work's catalogue identifier.

## Facsimile and page boundaries

Use the following conventions consistently:

- Each source page is represented by one `surface` with a `graphic` and measure zones.
- `surface/@corresp` points to the exact IIIF Presentation canvas; `graphic/@target` points to the image service.
- Every measure points to its measure zone through `measure/@facs`.
- Use one numbered `pb` for the first encoded content on every surface.
- Use `sb` for the remaining original system boundaries on that surface.
- `surface/@n` and `pb/@n` form a work-local sequence beginning with `1`.
- Record the original printed range in `sourceDesc/biblScope`; do not overload the local page sequence with printed pagination.

## Publication validation

Before changing a work's status to `finalized`, confirm all of the following:

1. The file is well-formed XML and validates against MEI 5.1 CMN.
2. All `xml:id` values are unique and all local references resolve.
3. Every measure has one valid facsimile zone and the zone is on the active surface.
4. Surface and `pb` sequences agree, with one `pb` per surface.
5. Work declarations, responsibilities, dates, identifiers, source range, and canonical URI have been reviewed by an editor.
6. Verovio renders the complete file without warning or error logs.
7. The notation has been compared visually with the facsimile; an empty automated report does not establish musical accuracy.
