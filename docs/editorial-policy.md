# Editorial policy and source register

This corpus is a corrected digital edition of the music printed in DdT, first series, volume 11 (1903), edited by Carl Stiehl. The edition preserves that source's musical presentation, including its keyboard realizations, while documenting substantive emendations. Relevant historical prints are used selectively as comparative witnesses when notation in DdT cannot be resolved clearly. This practice does not imply complete collation with the Uppsala prints; record the actual consultation for each work. Musical coherence supplies a rationale for a conjecture; source comparison establishes whether a reading is supported by a witness.

This policy was established following the pilot review and the editor's source clarification on 2026-09-29. Its adoption does not assert that every existing file has already been fully collated or every annotation revised.

## Sources and their roles

Use `src.ddt1903` for the 1903 DdT edition. It supplies the base score, its printed keyboard realization, and the existing BSB facsimile/measure-zone mapping. Keep its full description and separate image-use statement in `sourceDesc`.

Use the following additional source IDs for the historical prints. The locally supplied TIFFs reproduce the STIMU facsimile editions (Utrecht, 1991, introduction by Kerala J. Snyder), which in turn reproduce the Uppsala copies. Keep the historical witness and modern carrier distinct; see [the scan and conversion guide](uppsala-facsimiles.md). The source IDs below identify the historical witnesses:

- `src.uppsala.op1`: Dieterich Buxtehude, *VII. Suonate a doi, violino & viola da gamba, con cembalo ... opera prima*. Lübeck [1696]. RISM A/I B5204. Uppsala University Library (S-Uu), Düben Collection, `Uimtr 52:1–4`.
- `src.uppsala.op2`: Dieterich Buxtehude, *VII. Suonate a due, violino et viola da gamba con cembalo ... opera secunda*. Lübeck 1696. RISM A/I B5205. Uppsala University Library (S-Uu), Düben Collection, `Uimtr 52:1–4`.

These descriptions are corroborated by Maria Schildt's [Printed Music in the Düben Collection, page 2](https://www2.musik.uu.se/duben/Printed%20music%20in%20the%20Duben%20Collection2024.pdf), linked from the [Düben catalogue](https://www2.musik.uu.se/duben/Duben.php). The catalogue lists the same shelfmark range for the two separate opus entries; preserve their distinct RISM identifiers and source IDs. B5204 and B5205 are printed-catalogue identifiers, not assumed RISM Online record URLs.

Preserve the supplied brackets in Op. I's `[1696]`. In the source description, the numeric value may be normalized to `isodate="1696"` while the text and `type="catalogue-supplied"` retain its bibliographic status. This is the date attached to the catalogued witness, not a claim about the work's composition date or the resolution of every historical dating question. The titles above retain the catalogue's abbreviations; replace them with fuller transcriptions only after checking the scans.

For individual corrections, cite the relevant opus, partbook/instrument, printed page or folio, and local musical location. If a scan has no printed pagination, record an explicitly labelled image sequence or stable scan identifier. Avoid an unqualified “1696 print” because it does not distinguish the two sources. Record what was actually consulted, and distinguish direct consultation of a scan from reliance on another editor's report.

The sonata witnesses do not automatically describe sources of the appendix works. Add the actual manuscript or other witness when an appendix reading is supported by it.

## Reusable MEI source descriptions

Insert the appropriate `source` as a sibling of `src.ddt1903` within `fileDesc/sourceDesc`. Include both only when both were actually used for the encoded work. These entries deliberately contain catalogue links without fabricated image URLs.

```xml
<source xml:id="src.uppsala.op1" type="historical-print">
   <bibl>
      <title>VII. Suonate a doi, violino &amp; viola da gamba, con cembalo ... opera prima</title>
      <composer>Dieterich Buxtehude</composer>
      <imprint>
         <pubPlace>Lübeck</pubPlace>
         <date isodate="1696" type="catalogue-supplied">[1696]</date>
      </imprint>
      <identifier type="RISM-A-I">B5204</identifier>
      <physLoc>
         <repository>Uppsala University Library, Düben Collection</repository>
         <identifier type="RISM-siglum">S-Uu</identifier>
         <identifier type="shelfmark">Uimtr 52:1–4</identifier>
      </physLoc>
      <ref type="catalogue" target="https://www2.musik.uu.se/duben/Printed%20music%20in%20the%20Duben%20Collection2024.pdf">Printed Music in the Düben Collection, p. 2</ref>
      <availability>
         <useRestrict>This witness was consulted through the STIMU facsimile edition (Utrecht, 1991, introduction by Kerala J. Snyder). TIFFs were made by the editor’s university library; public redistribution terms for the images remain unconfirmed.</useRestrict>
      </availability>
   </bibl>
</source>
```

```xml
<source xml:id="src.uppsala.op2" type="historical-print">
   <bibl>
      <title>VII. Suonate a due, violino et viola da gamba con cembalo ... opera secunda</title>
      <composer>Dieterich Buxtehude</composer>
      <imprint>
         <pubPlace>Lübeck</pubPlace>
         <date isodate="1696">1696</date>
      </imprint>
      <identifier type="RISM-A-I">B5205</identifier>
      <physLoc>
         <repository>Uppsala University Library, Düben Collection</repository>
         <identifier type="RISM-siglum">S-Uu</identifier>
         <identifier type="shelfmark">Uimtr 52:1–4</identifier>
      </physLoc>
      <ref type="catalogue" target="https://www2.musik.uu.se/duben/Printed%20music%20in%20the%20Duben%20Collection2024.pdf">Printed Music in the Düben Collection, p. 2</ref>
      <availability>
         <useRestrict>This witness was consulted through the STIMU facsimile edition (Utrecht, 1991, introduction by Kerala J. Snyder). TIFFs were made by the editor’s university library; public redistribution terms for the images remain unconfirmed.</useRestrict>
      </availability>
   </bibl>
</source>
```

## Scan access and redistribution

The TIFFs were made by the editor's university library from the 1991 STIMU books; the accompanying reuse terms are not known. Clarify those terms with the digitising library before public distribution. The scanned modern introduction has its own rights, and scan 4 in each volume combines modern and historical content. The [scan guide](uppsala-facsimiles.md) records the edition evidence, historical/modern distinctions and preliminary EU/German rights assessment. Uppsala's [catalogue contact guidance](https://www2.musik.uu.se/duben/Duben.php) remains relevant if further images or information are sought directly from Uppsala.

The source descriptions and reading citations can be published while the scans remain outside the public repository. When terms are confirmed, retain the library's attribution and permitted-use wording, identify the scan set covered, and update the source availability statement. Keep private correspondence outside public Git history; a public summary of the confirmed terms can accompany the images.

Public IIIF endpoints for these prints have not been established in this review. The [current catalogue landing page](https://catmus.musik.uu.se/en) distinguishes its digitized manuscript database from the complementary PDF list of printed music; a print entry alone does not identify an image service.

MEI can link ordinary images using `graphic/@target`; IIIF is optional. After permission/terms are settled, possible delivery locations include an institutional service, a versioned archival deposit, static hosting, or an optional image bundle. A repository directory is also possible when its size and distribution model suit the scans. Keep public score releases usable without access to private local image paths. Do not point `graphic/@target` at catalogue pages or PDF catalogue entries in place of actual page images. [MEI graphic reference](https://music-encoding.org/guidelines/v5/elements/graphic.html).

## Correction categories

Use the following distinctions consistently:

1. **OMR or conversion repair:** the encoding is brought into agreement with DdT. Routine repairs can be summarized in revision history and do not each need a published annotation. An ambiguous repair still warrants a local note.
2. **Source-supported emendation:** the encoded reading departs from DdT and is attested by an identified historical witness. Record both readings and the exact evidence location.
3. **Conjectural emendation:** the encoded reading departs from DdT on rhythmic, harmonic, contrapuntal, or other stated grounds without direct witness support. State the reasoning and uncertainty. Prefer the smallest justified intervention and retain a recoverable account of the printed reading.
4. **Retained source reading:** a noteworthy source feature or apparent anomaly is preserved deliberately. Record it when it could otherwise be mistaken for an encoding error. A checker warning may remain as a documented exception.
5. **Encoding note:** the musical reading is preserved but its technical representation, such as a cross-staff tie, needs explanation or has a known renderer limitation.
6. **Unresolved reading:** evidence is insufficient to choose confidently. Mark the uncertainty and record the available readings. Release review must explicitly address it; successful rhythm checks alone do not resolve it.

In particular, DdT's realization is source content for this edition. A change to that realization is a departure from DdT even though the historical print has no realization. Absence from the historical print does not support a particular corrected chord or rhythm. The measure-97 removal of a dot in the pilot should therefore be reviewed as a conjectural emendation supported by a stated rhythmic argument. The measure-11 correction is recorded as source-supported: the C-sharp4 is an eighth note in the Violino partbook, Sonata I, opening music page (signature A), third system, first bar; local Op. I `scan-0006.jpg`, right-hand page, reproduces that location through STIMU 1991. The measure-79 tie explanation is an encoding note. On 2026-10-01 the editor confirmed joint responsibility by Egor Polyakov and Francy Häring for all three decisions. The pilot annotations now identify both responsibility declarations. This metadata completion does not constitute final publication sign-off.

## Recording decisions in MEI

Use one authoritative annotation in the MEI for each substantive decision, attached through `plist` (or an appropriate event pointer) to stable IDs. A corpus-wide list of emendations can be generated from these annotations; avoid manually maintaining a second list that can diverge.

Keep `type="editorial"` for compatibility. Adopt these project-specific `label` values for the categories above: `source-supported-emendation`, `conjectural-emendation`, `source-reading`, `encoding-note`, and `unresolved-reading`. An optional `omr-correction` label can identify a noteworthy recognition repair. These labels are CAMAT conventions, not MEI-defined controlled values.

For an emendation, the annotation must record:

- DdT's reading and the encoded replacement, with enough pitch/duration/context information to reconstruct the difference;
- a precise witness/partbook/page locator when a witness supports the change, or the conjectural rationale otherwise;
- the responsible editor through `resp` and any relevant uncertainty in the text;
- the affected event IDs and, when useful, a link to the corresponding source image/zone.

Use `annot/@source` only for sources that actually attest the reading in question. Use `ref/@target` inside the explanation to discuss contextual or contrasting evidence. Link `resp` to the actual responsible header declaration; do not infer the editor from who most recently saved the file. Review dates and review responsibility can be recorded in a meaningful revision entry.

The following illustration uses the existing measure-97 chord ID and the template's generic `resp.editor`; the responsibility pointer must be replaced by the verified editor's declaration before application. It is a documentation example, not an applied correction or completed review:

```xml
<annot xml:id="editorial.m97.example" type="editorial"
       label="conjectural-emendation"
       plist="#bsb00023199_00018_facs_zones_dfki3"
       resp="#resp.editor">
   <p>DdT prints this chord as a dotted eighth note. The dot is omitted
      in the encoding to restore rhythmic consistency in this layer.
      This is a conjectural emendation of DdT's keyboard realization.
      The <ref target="#src.uppsala.op1">Op. I historical print</ref>
      transmits the continuo part but no keyboard realization and
      therefore does not attest the replacement rhythm.</p>
</annot>
```

Expand the rhythmic rationale with the actual beat/layer accounting during review. Do not introduce a spurious `source` pointer suggesting that the historical print contains the realized chord.

For a release designed to expose selectable alternatives, encode the original and corrected passages with `choice/sic/corr`, or use `app/lem/rdg` for source variants. That requires a documented default reading and tested selection in both the renderer and CAMAT. A corrected reading with complete, addressable annotations is the current lightweight policy. [MEI scholarly editing](https://music-encoding.org/guidelines/v5/content/scholarlyediting.html), [MEI annotation attributes](https://music-encoding.org/guidelines/v5/elements/annot.html).

## Staff layout and analytical views

Preserve the five-staff DdT presentation in the Op. I/1 master file. Its two lower staves reproduce the realization printed in DdT; they should not be removed merely because the earlier partbooks contain continuo only. Treat DdT as the source of that realization without assigning its individual authorship more specifically than the evidence supports.

For the pilot, document these roles: staff 1 violin; staff 2 viola da gamba; staff 3 figured continuo bass; staves 4 and 5 upper and lower realization staves. Do not assume those staff numbers apply to every appendix work. Store per-work roles in the release manifest or an equivalent declared mapping. Preserve source labels in the master when fidelity requires it; provide readable analytical names in the consumer/derived view. The current CAMAT mapper's fallback to opaque staff IDs is a consumer-metadata issue rather than evidence of incorrect engraving.

Specify the selected view with each analysis: for example, the encoded violin/gamba/continuo material, or DdT's complete texture including the realization. A selection of the first three staves is still derived from this corrected DdT edition; it is not automatically an independent diplomatic transcription of the original partbooks.

## Release review

Before finalization, review substantive annotations against the cited evidence, confirm responsibilities, and disclose retained anomalies or unresolved readings. Record the extent of source comparison accurately: consulting selected passages is different from collating every note. Independent review by a second editor is desirable for conjectural changes when available, but the header must record the review actually performed.

The MEI header carries a concise policy summary. This document carries the fuller corpus policy. Keep the two consistent, and record substantive policy changes with the next corpus/profile version.
