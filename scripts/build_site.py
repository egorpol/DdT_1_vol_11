#!/usr/bin/env python3
"""Assemble the static web viewer for GitHub Pages.

Copies site/ (the viewer), the assembled MEI files listed in
validation/editorial-works.json, supplemental_material/manifest.json and the
excerpt images it lists into OUT, and writes OUT/works.json, the index the
viewer's work selector reads. Each excerpt is checked against its SHA-256 and
pixel size in the manifest, and its measure, event and note against its MEI
file. The facsimile pages are not copied: the viewer loads them from
the BSB IIIF server. OUT is emptied first.

Standard library only.

Usage: python scripts/build_site.py [OUT]    (default: _site)
Preview: python -m http.server -d _site, then open http://localhost:8000/
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_FILES = ["index.html", "viewer.css", "viewer.js"]
WORK_LIST = "validation/editorial-works.json"
EXCERPTS = "supplemental_material/manifest.json"
MEI = "{http://www.music-encoding.org/ns/mei}"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII"}
# Works without an assembled file; the README's work table lists the same.
# An entry drops out once its work is in the work list.
PENDING = [
    {
        "key": "op2_01_sonata_b_flat_major",
        "title": "Sonata I in B-flat major, Op. II",
        "catalogue": "BuxWV 259",
        "pages": {"from": "79", "to": "89"},
        "status": "pending",
    },
]
ORDER = ["op1", "op2", "app"]


def short_key(key: str) -> str:
    """op1_01_sonata_f_major -> op1_01, the form used in viewer links."""
    return "_".join(key.split("_")[:2])


def label(key: str) -> str:
    match = re.fullmatch(r"(?:op(\d)|app)_(\d\d)", short_key(key))
    number = ROMAN[int(match.group(2))]
    return f"Op. {ROMAN[int(match.group(1))]}/{int(match.group(2))}" if match.group(1) else f"App. {number}"


def mei_title(path: Path) -> str:
    title = ET.parse(path).getroot().find(f"{MEI}meiHead/{MEI}fileDesc/{MEI}titleStmt/{MEI}title")
    return " ".join("".join(title.itertext()).split())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path.relative_to(ROOT)} is not a PNG file")
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def check_excerpt(item: dict, files: dict[str, str]) -> None:
    """The excerpt's file, size, measure, event and note match the manifest."""
    where = f"{EXCERPTS}, {item['file']}"
    source = ROOT / item["file"]
    if sha256(source) != item["sha256"]:
        raise SystemExit(f"{where}: does not match its SHA-256")
    if png_size(source) != (item["width"], item["height"]):
        raise SystemExit(f"{where}: image is {'x'.join(map(str, png_size(source)))}, not {item['width']}x{item['height']}")
    if files.get(item["work_key"]) != item["mei_file"]:
        raise SystemExit(f"{where}: {item['mei_file']} is not the listed file of {item['work_key']}")
    root = ET.parse(ROOT / item["mei_file"]).getroot()
    measure = next((m for m in root.iter(f"{MEI}measure") if m.get("n") == str(item["measure"])), None)
    if measure is None:
        raise SystemExit(f"{where}: no measure {item['measure']} in {item['mei_file']}")
    if not any(el.get(XML_ID) == item["event_id"] for el in measure.iter()):
        raise SystemExit(f"{where}: no event {item['event_id']} in measure {item['measure']}")
    if item.get("annotation_id") and not any(a.get(XML_ID) == item["annotation_id"] for a in root.iter(f"{MEI}annot")):
        raise SystemExit(f"{where}: no annot {item['annotation_id']} in {item['mei_file']}")


def copy(source: Path, out: Path, target: str) -> None:
    destination = out / target
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    print(f"{source.relative_to(ROOT)} -> {target}")


def build(out: Path) -> dict:
    for name in SITE_FILES:
        copy(ROOT / "site" / name, out, name)

    works = []
    for work in json.loads((ROOT / WORK_LIST).read_text(encoding="utf-8"))["works"]:
        source = ROOT / work["file"]
        target = f"mei/{source.name}"
        copy(source, out, target)
        works.append({
            "key": work["key"],
            "title": mei_title(source),
            "catalogue": work["catalogue"],
            "pages": work["printed_page_range"],
            "status": work["editorial_status"],
            "mei": target,
            "source": work["file"],
            "report": work["file"].removesuffix(".mei") + "_consistency_report.csv",
        })
    works += [w for w in PENDING if w["key"] not in {x["key"] for x in works}]
    for work in works:
        work["id"] = short_key(work["key"])
        work["label"] = label(work["key"])
    works.sort(key=lambda w: (ORDER.index(w["id"].split("_")[0]), w["id"]))

    manifest = json.loads((ROOT / EXCERPTS).read_text(encoding="utf-8"))
    files = {w["key"]: w["source"] for w in works if "mei" in w}
    for item in manifest["items"]:
        check_excerpt(item, files)
        copy(ROOT / item["file"], out, item["file"])
    copy(ROOT / EXCERPTS, out, EXCERPTS)

    index = {"works": works}
    (out / "works.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"works.json: {len(works)} works, {sum('mei' in w for w in works)} with MEI")
    return index


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "_site").resolve()
    # OUT is emptied: inside the repository only _site may be used.
    if ROOT.is_relative_to(out) or (out.is_relative_to(ROOT) and not out.is_relative_to(ROOT / "_site")):
        print(f"refusing to empty {out}", file=sys.stderr)
        return 1
    if out.exists():
        shutil.rmtree(out)
    build(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
