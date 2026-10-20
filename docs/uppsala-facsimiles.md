# Uppsala witnesses through the STIMU 1991 facsimiles

## What these TIFFs contain

The two supplied directories contain photographs/scans of the **STIMU facsimile
edition, Utrecht, 1991, with an introduction by Kerala J. Snyder**. They are not
direct photographs of the seventeenth-century originals. The historical copies
reproduced by STIMU are held at Uppsala University Library. The scanned modern
books carry Musikhochschule Lübeck library stamps. The editor clarified on
2026-10-01 that the TIFFs were made by their university library; reuse terms and
the precise digitising institution have not been established.

Evidence in each volume: scan 2, right side, identifies the modern edition; scan
4, left side, includes the introduction's July 1991 signature and the STIMU
copyright/imprint. The introduction says that STIMU reproduced the Uppsala copy
and changed the physical format. Snyder's
[bibliography](https://sscm-sscm.org/about-us/honorary-members/kerala-j-snyder-selected-bibliography/)
and the recording publisher's
[edition citation](https://dacapo-records.dk/en/recordings/buxtehude-complete-chamber-music-vol-1)
corroborate the publisher, year and introduction author.

Keep `src.uppsala.op1` / `src.uppsala.op2` for the historical witnesses. Use
`src.stimu1991.op1` / `src.stimu1991.op2` to identify the modern carriers when
describing how those witnesses were consulted. These new IDs are documented in
the image configuration; no MEI header has been changed automatically. Record
the facsimile edition alongside the historical witness and say explicitly that
comparison used the STIMU reproduction.

There is a dating distinction to resolve bibliographically: STIMU's modern
Op. I title gives **Hamburg [1694]**, while the Uppsala printed-music catalogue
cited in the existing editorial policy gives **Lübeck [1696]**. Preserve both
attributed statements; do not silently replace the catalogue's date or turn
the facsimile publication date into the historical witness date. Op. II's modern
title gives Hamburg 1696. The historic title pages describe printing in Hamburg
and sale in Lübeck. This inventory does not resolve the Op. I dating question.

## Directory layout

Keep the TIFF masters in their delivered directories for now. The converter
never changes, moves or recompresses them. Keep backups outside normal Git
history. The received files total 7,105,854,304 bytes: 42 single-frame RGB TIFFs
for Op. I (300 dpi) and 56 for Op. II (400 dpi). Most TIFFs contain a two-page
spread. A scan number is therefore not a printed page number.

```text
Polyakov, Buxtehude1/              received TIFF masters, local
Polyakov, Buxtehude2/              received TIFF masters, local
facsimiles/uppsala/
  sources.json                    source/carrier identity and inspected front matter
  op1/
    inventory-jpeg.json           original/output hashes and conversion metadata
    jpeg/scan-0001.jpg            full-resolution access image
    jpeg/scan-0002.jpg
    ...
  op2/
    inventory-jpeg.json
    jpeg/scan-0025.jpg
    jpeg/scan-0025a.jpg            inserted scan retained without renumbering
    ...
```

PNG runs create `png/` and `inventory-png.json` alongside the JPEG derivative.
The configuration and this guide are intended for Git; original TIFFs and the
generated volume folders are ignored while distribution is unresolved. No
license for the MEI data is applied to these images.

## Convert and rerun

Use the Python environment that contains CAMAT's validation dependencies;
Pillow is the converter's only non-standard dependency. If necessary:

```sh
python -m pip install "Pillow>=10.4"
```

From the repository root:

```sh
python scripts/convert_uppsala_scans.py --dry-run
python scripts/convert_uppsala_scans.py
python scripts/convert_uppsala_scans.py --opus 1 --format png
```

Default: both volumes, full original pixel dimensions, JPEG quality 95, no
chroma subsampling. JPEG is lossy: use it for viewing, while retaining TIFF
masters for evidence. PNG provides a lossless pixel derivative of the current
8-bit RGB inputs, but does not retain all TIFF-specific metadata. Neither
format claims to be a replacement archival master. DPI and ICC profiles are
retained when present. TIFF orientation is applied to the derivative; scan
content is not cropped, split, deskewed, sharpened or binarized.

For a smaller viewing set, supply `--max-edge 4000`. To change an existing set's
settings, use `--overwrite` deliberately or edit the configuration to choose
a separate output directory. Resizing changes coordinates for future image
zones; keep each zone mapping tied to the image dimensions it was drawn on.

Rerunning with identical source bytes, settings, script and Pillow version
verifies the source and derivative hashes and reuses the images. Unrecorded
outputs, changed TIFFs, changed derivatives and changed software/settings are
reported as conflicts; `--overwrite` regenerates derivatives only. Conversion
is checkpointed per TIFF, including all frames, so completed scans can be
reused after an interruption. Removed input files do not cause image deletion.

The inventories record input/output paths and SHA-256, bytes, frame numbers,
dimensions, modes, bit depth, orientation, TIFF compression, DPI and ICC hash,
plus conversion settings/software. Printed page labels remain unset until
actually inspected. Front-matter classifications come from `sources.json`;
other scans remain `not-reviewed`. Conversion does not certify redistribution.

## Historical pages and modern material

Scans 1–3 of both volumes contain modern covers, title pages or introduction.
Scan 4 is **mixed**: modern introduction/copyright on the left, historical title
page on the right. Excluding only the first three files would still reproduce
the modern introduction. A later public selection needs either a reviewed crop
of scan 4's historical right side or omission of the entire mixed spread.
Record crop coordinates and provenance if that derivative is made. Do not
auto-split at an assumed centre line. Historical title pages, dedications and
musical pages can be useful evidence; musical pages alone are not the whole
historical witness.

## Reuse assessment as of 2026-10-01

Buxtehude's historical music and its original print are in the public domain.
STIMU's 1991 notice does not create fresh copyright in the old composition.
Snyder's modern introduction is a separate authored text and should be treated
as protected; copyright normally lasts 70 years after the author's death in
Germany ([UrhG § 64](https://www.gesetze-im-internet.de/urhg/__64.html)).

EU [Directive 2019/790, Article 14](https://eur-lex.europa.eu/eli/dir/2019/790/oj)
addresses reproductions of public-domain **works of visual art**, with an
exception for original new works. German
[UrhG § 68](https://www.gesetze-im-internet.de/urhg/__68.html) excludes related-right
protection for reproductions of public-domain visual works. Applying those
provisions automatically to every photograph of printed music would require
an additional legal assessment; a public-domain composition alone does not
establish that every book photograph falls within that category.

Other rights have their own tests and terms. German scientific-edition
protection, where its criteria are met, lasts 25 years after publication
([UrhG § 70](https://www.gesetze-im-internet.de/urhg/BJNR012730965.html));
any such term running from a 1991 publication would have expired after 2016.
That does not dispose of copyright in the introduction or separate photographic
rights. German [UrhG § 72](https://www.gesetze-im-internet.de/urhg/__72.html)
can protect qualifying photographs for 50 years; whether the particular
reproduction process qualifies and whether § 68 applies need to be established.
Any library scan-supply agreement is a separate question.

These observations are a preliminary Germany/EU assessment, not a determination
of the particular files' legal status. The present practical conclusion is
**local conversion and source comparison can proceed; public redistribution
has not been cleared**. Ask the university library which reuse terms apply to
the TIFFs and converted/cropped copies, who controls any photograph rights,
and whether its permission covers the historical facsimile pages specifically.
If legal clearance rather than permission is relied on, document that basis
for the selected images and relevant jurisdiction. Keep Snyder's introduction
out of a historical-facsimile-only publication unless separately authorized.
