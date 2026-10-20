import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/convert_uppsala_scans.py'
spec = importlib.util.spec_from_file_location('scan_conversion', SCRIPT)
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


def volume(root):
    (root / 'input').mkdir()
    return {'key': 'op2', 'source_id': 'src.uppsala.op2', 'carrier_id': 'src.stimu1991.op2',
            'input_dir': 'input', 'output_dir': 'out'}


def test_natural_order_and_inserted_scan_names():
    paths = [Path(name) for name in ('2.10.tif', '2.25a.tif', '2.2.tif', '2.25.tif')]
    assert [p.name for p in sorted(paths, key=converter.natural_key)] == [
        '2.2.tif', '2.10.tif', '2.25.tif', '2.25a.tif']
    assert converter.image_stem(Path('2.25a.tif')) == 'scan-0025a'


def test_lossless_all_frames_hashes_and_resume(tmp_path):
    v = volume(tmp_path)
    p = tmp_path / 'input/2.25a.tif'
    images = [Image.new('RGB', (23, 17), c) for c in ('red', 'blue')]
    images[0].save(p, save_all=True, append_images=images[1:], dpi=(300, 300))
    original = p.read_bytes()
    result = converter.convert_volume(v, root=tmp_path, output_format='png')
    assert result['converted'] == 2
    inventory = json.loads((tmp_path / 'out/inventory-png.json').read_text())
    assert len(inventory['scans']) == 1
    frames = inventory['scans'][0]['frames']
    for index, entry in enumerate(frames):
        target = tmp_path / entry['file']
        assert f'scan-0025a-frame-{index + 1:03d}.png' == target.name
        with Image.open(target) as actual:
            assert actual.tobytes() == images[index].tobytes()
        assert converter.sha256(target) == entry['sha256']
    assert p.read_bytes() == original
    assert converter.convert_volume(v, root=tmp_path, output_format='png')['reused'] == 2


def test_dry_run_does_not_create_output(tmp_path):
    v = volume(tmp_path)
    Image.new('RGB', (10, 12), 'white').save(tmp_path / 'input/2.1.tif')
    converter.convert_volume(v, root=tmp_path, dry_run=True)
    assert not (tmp_path / 'out').exists()


def test_changed_derivative_requires_explicit_overwrite(tmp_path):
    v = volume(tmp_path)
    Image.new('RGB', (20, 12), 'white').save(tmp_path / 'input/2.1.tif')
    converter.convert_volume(v, root=tmp_path)
    target = tmp_path / 'out/jpeg/scan-0001.jpg'
    target.write_bytes(b'broken')
    with pytest.raises(ValueError, match='Input/output changed'):
        converter.convert_volume(v, root=tmp_path)
    assert converter.convert_volume(v, root=tmp_path, overwrite=True)['converted'] == 1


def test_changed_settings_require_explicit_overwrite(tmp_path):
    v = volume(tmp_path)
    Image.new('RGB', (20, 12), 'white').save(tmp_path / 'input/2.1.tif')
    converter.convert_volume(v, root=tmp_path)
    with pytest.raises(ValueError, match='settings/source/software changed'):
        converter.convert_volume(v, root=tmp_path, max_edge=10)


def test_changed_source_requires_overwrite_and_keeps_new_master(tmp_path):
    v = volume(tmp_path)
    source = tmp_path / 'input/2.1.tif'
    Image.new('RGB', (20, 12), 'white').save(source)
    converter.convert_volume(v, root=tmp_path)
    Image.new('RGB', (20, 12), 'black').save(source)
    original = source.read_bytes()
    with pytest.raises(ValueError, match='Input/output changed'):
        converter.convert_volume(v, root=tmp_path)
    converter.convert_volume(v, root=tmp_path, overwrite=True)
    assert source.read_bytes() == original


def test_collision_detected_before_writing(tmp_path):
    v = volume(tmp_path)
    for name in ('2.1.tif', '2.01.tif'):
        Image.new('RGB', (10, 12), 'white').save(tmp_path / 'input' / name)
    with pytest.raises(ValueError, match='collide'):
        converter.convert_volume(v, root=tmp_path)
    assert not (tmp_path / 'out').exists()


def test_output_cannot_overlap_tiff_master_directory(tmp_path):
    v = volume(tmp_path)
    v['output_dir'] = 'input/converted'
    with pytest.raises(ValueError, match='must be separate'):
        converter.convert_volume(v, root=tmp_path)


def test_resized_derivative_preserves_aspect_ratio_and_physical_size(tmp_path):
    v = volume(tmp_path)
    Image.new('RGB', (100, 40), 'white').save(tmp_path / 'input/2.1.tif', dpi=(300, 300))
    converter.convert_volume(v, root=tmp_path, max_edge=50)
    with Image.open(tmp_path / 'out/jpeg/scan-0001.jpg') as image:
        assert image.size == (50, 20)
        assert image.info['dpi'] == (150, 150)
