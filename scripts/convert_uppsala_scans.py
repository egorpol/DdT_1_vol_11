#!/usr/bin/env python3
"""Convert the locally held STIMU/Uppsala TIFFs without altering their masters.

Requires Pillow. See docs/uppsala-facsimiles.md for provenance and image selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps, __version__ as PILLOW_VERSION

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def natural_key(path: Path):
    return tuple((0, int(s)) if s.isdigit() else (1, s.casefold())
                 for s in re.split(r'(\d+)', path.name))


def image_stem(path: Path) -> str:
    # Preserve inserted scans, e.g. 2.25a.tif -> scan-0025a, without renumbering.
    match = re.fullmatch(r'\d+\.(\d+)([a-zA-Z]*)', path.stem)
    if match:
        return f'scan-{int(match[1]):04d}{match[2].lower()}'
    return 'scan-' + re.sub(r'[^a-zA-Z0-9._-]+', '_', path.stem).strip('._-')


def atomic_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     suffix='.json.tmp', delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def display_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)


def prepare_image(frame: Image.Image, *, output_format: str, max_edge: int | None):
    image = ImageOps.exif_transpose(frame)
    if output_format == 'jpeg':
        if image.mode in ('I', 'F') or image.mode.startswith('I;16'):
            raise ValueError('High-bit-depth TIFF requires PNG or an explicit tonal conversion.')
        if 'A' in image.getbands() or 'transparency' in image.info:
            rgba = image.convert('RGBA')
            image = Image.new('RGB', rgba.size, 'white')
            image.paste(rgba, mask=rgba.getchannel('A'))
        elif image.mode not in ('RGB', 'L'):
            image = image.convert('RGB' if image.mode != '1' else 'L')
    elif image.mode not in ('1', 'L', 'LA', 'P', 'RGB', 'RGBA', 'I', 'I;16'):
        raise ValueError(f'PNG cannot preserve {image.mode} pixels; review this TIFF separately.')
    if max_edge and max(image.size) > max_edge:
        image = image.copy()
        image.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
    return image


def make_plan(volume: dict, *, root: Path, output_format: str):
    source_dir = (root / volume['input_dir']).resolve()
    output_base = (root / volume['output_dir']).resolve()
    if not source_dir.is_dir():
        raise FileNotFoundError(f'Missing TIFF directory: {source_dir}')
    if output_base == source_dir or output_base.is_relative_to(source_dir) or source_dir.is_relative_to(output_base):
        raise ValueError('TIFF master and derivative directories must be separate.')
    paths = sorted((p for p in source_dir.iterdir() if p.is_file()
                    and p.suffix.lower() in ('.tif', '.tiff')), key=natural_key)
    if not paths:
        raise ValueError(f'No TIFF files in {source_dir}')
    extension = 'jpg' if output_format == 'jpeg' else 'png'
    plan, targets = [], set()
    for path in paths:
        with Image.open(path) as image:
            count = image.n_frames
        outputs = []
        for index in range(count):
            suffix = f'-frame-{index + 1:03d}' if count > 1 else ''
            target = output_base / output_format / f'{image_stem(path)}{suffix}.{extension}'
            if target in targets:
                raise ValueError(f'TIFF names collide at {target}')
            targets.add(target)
            outputs.append(target)
        plan.append((path, outputs))
    return plan, output_base / f'inventory-{output_format}.json'


def convert_volume(volume: dict, *, root: Path = ROOT, output_format='jpeg',
                   quality=95, max_edge=None, overwrite=False, dry_run=False):
    root = Path(root).resolve()
    plan, inventory_path = make_plan(volume, root=root, output_format=output_format)
    options = {'format': output_format, 'max_edge': max_edge, 'orientation': 'apply-TIFF-orientation',
               'quality': quality if output_format == 'jpeg' else None,
               'subsampling': 0 if output_format == 'jpeg' else None}
    if dry_run:
        print(f"{volume['key']}: {len(plan)} TIFFs -> {sum(len(o) for _, o in plan)} {output_format} images")
        print(f'  {display_path(inventory_path.parent / output_format, root)}')
        print('  Full resolution' if max_edge is None else f'  Maximum image edge: {max_edge} pixels')
        return {'converted': 0, 'reused': 0, 'files': len(plan), 'dry_run': True}
    old = json.loads(inventory_path.read_text()) if inventory_path.exists() else {}
    converter_digest = sha256(Path(__file__))
    if old and (old.get('options') != options or old.get('source_id') != volume['source_id']
                or old.get('carrier_id') != volume['carrier_id']
                or old.get('converter_sha256') != converter_digest
                or old.get('pillow_version') != PILLOW_VERSION) and not overwrite:
        raise ValueError(f'Conversion settings/source/software changed at {inventory_path}; use --overwrite to regenerate.')
    previous = {row['input']: row for row in old.get('scans', [])}
    # Refuse unrecorded output files before writing any images for this volume.
    for source, outputs in plan:
        recorded = {f['file'] for f in previous.get(display_path(source, root), {}).get('frames', [])}
        for target in outputs:
            if target.exists() and display_path(target, root) not in recorded and not overwrite:
                raise FileExistsError(f'Unrecorded derivative exists: {target}; use --overwrite deliberately.')
    inventory = {'schema_version': 1, 'source_id': volume['source_id'],
                 'carrier_id': volume['carrier_id'], 'volume': volume['key'],
                 'publication_status': 'not-reviewed-for-redistribution',
                 'options': options, 'pillow_version': PILLOW_VERSION,
                 'converter_sha256': converter_digest, 'scans': []}
    conversion_identity = {'options': options, 'converter_sha256': converter_digest,
                           'pillow_version': PILLOW_VERSION}
    counts = {'converted': 0, 'reused': 0, 'files': len(plan)}
    # Keep old entries while checkpointing so an interrupted run can resume.
    checkpoints = dict(previous)
    for position, (source, outputs) in enumerate(plan, 1):
        source_name = display_path(source, root)
        digest = sha256(source)
        prior = previous.get(source_name)
        reusable = (not overwrite and old.get('options') == options and prior
                    and prior.get('conversion') == conversion_identity
                    and prior.get('input_sha256') == digest
                    and [f['file'] for f in prior.get('frames', [])] == [display_path(p, root) for p in outputs]
                    and all(p.is_file() and sha256(p) == f['sha256']
                            for p, f in zip(outputs, prior.get('frames', []))))
        if reusable:
            row = dict(prior)
            counts['reused'] += len(outputs)
            action = 'verified/reused'
        else:
            # A changed input or derivative is an explicit conflict, not silent repair.
            if any(p.exists() for p in outputs) and not overwrite:
                raise ValueError(f'Input/output changed for {source.name}; use --overwrite to regenerate.')
            row = {'input': source_name, 'input_sha256': digest, 'input_bytes': source.stat().st_size,
                   'conversion': conversion_identity, 'frames': []}
            with Image.open(source) as tiff:
                for frame_index, target in enumerate(outputs):
                    tiff.seek(frame_index)
                    tags = tiff.tag_v2
                    metadata = {'frame': frame_index + 1, 'input_size': list(tiff.size), 'input_mode': tiff.mode,
                                'bits_per_sample': [int(n) for n in tags.get(258, ())],
                                'orientation': int(tags.get(274, 1)),
                                'compression': int(tags.get(259, 1)),
                                'dpi': [float(n) for n in tiff.info.get('dpi', ())],
                                'icc_profile_sha256': hashlib.sha256(tiff.info['icc_profile']).hexdigest()
                                if tiff.info.get('icc_profile') else None}
                    frame = tiff.copy()
                    image = prepare_image(frame, output_format=output_format, max_edge=max_edge)
                    settings = {'format': 'JPEG' if output_format == 'jpeg' else 'PNG'}
                    if output_format == 'jpeg':
                        settings.update(quality=quality, subsampling=0, optimize=True)
                    if tiff.info.get('icc_profile'):
                        settings['icc_profile'] = tiff.info['icc_profile']
                    if tiff.info.get('dpi'):
                        scale = image.width / frame.width
                        settings['dpi'] = tuple(float(d) * scale for d in tiff.info['dpi'])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tempfile.NamedTemporaryFile(dir=target.parent, suffix='.image.tmp', delete=False) as stream:
                        temporary = Path(stream.name)
                    try:
                        image.save(temporary, **settings)
                        with Image.open(temporary) as verified:
                            verified.load()
                            if verified.size != image.size:
                                raise ValueError(f'Output dimensions differ at {target}')
                        temporary.replace(target)
                    finally:
                        temporary.unlink(missing_ok=True)
                    metadata.update(file=display_path(target, root), size=list(image.size), mode=image.mode,
                                    bytes=target.stat().st_size, sha256=sha256(target))
                    row['frames'].append(metadata)
                    counts['converted'] += 1
            if sha256(source) != digest:
                raise ValueError(f'TIFF changed during conversion: {source}')
            action = 'converted'
        row['scan_role'] = volume.get('scan_roles', {}).get(source.name, 'not-reviewed')
        row['printed_page_labels'] = None
        checkpoints[source_name] = row
        inventory['scans'] = list(checkpoints.values())
        inventory['verified_utc'] = datetime.now(timezone.utc).isoformat()
        atomic_json(inventory_path, inventory)
        print(f"{volume['key']} {position}/{len(plan)}: {source.name} {action}", flush=True)
    inventory['scans'] = [checkpoints[display_path(p, root)] for p, _ in plan]
    atomic_json(inventory_path, inventory)
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'facsimiles/uppsala/sources.json')
    parser.add_argument('--opus', choices=('all', '1', '2'), default='all')
    parser.add_argument('--format', choices=('jpeg', 'png'), default='jpeg')
    parser.add_argument('--quality', type=int, default=95, help='JPEG quality, 1–100; default 95, no chroma subsampling.')
    parser.add_argument('--max-edge', type=int, help='Optional resizing; default preserves full pixel dimensions.')
    parser.add_argument('--overwrite', action='store_true', help='Regenerate existing derivatives deliberately; never modify TIFFs.')
    parser.add_argument('--dry-run', action='store_true', help='Read TIFF headers and show the plan without creating files.')
    args = parser.parse_args(argv)
    if not 1 <= args.quality <= 100 or (args.max_edge is not None and args.max_edge < 1):
        parser.error('quality must be 1–100 and max-edge must be positive')
    try:
        config = json.loads(args.config.read_text(encoding='utf-8'))
        volumes = [v for v in config['volumes'] if args.opus == 'all' or str(v['opus']) == args.opus]
        if not volumes:
            raise ValueError('No matching volumes in the configuration.')
        for volume in volumes:
            counts = convert_volume(volume, output_format=args.format, quality=args.quality,
                                    max_edge=args.max_edge, overwrite=args.overwrite, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"{volume['key']}: {counts['converted']} converted, {counts['reused']} verified/reused")
    except (OSError, ValueError, KeyError) as exc:
        print(f'Conversion failed: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
