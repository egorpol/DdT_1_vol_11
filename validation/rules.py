"""Edition policy. All rules here belong to DdT; no composer assumptions in CAMAT."""
from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, unquote

MEI = 'http://www.music-encoding.org/ns/mei'
ID = '{http://www.w3.org/XML/1998/namespace}id'
NS = {'m': MEI}


def text(element):
    return ' '.join(''.join(element.itertext()).split()) if element is not None else ''


def find(root, path):
    return root.find('/'.join('m:' + part for part in path.split('/')), NS)


def reviewed(review, digest):
    if not isinstance(review, dict) or not review.get('reviewer') or review.get('input_sha256') != digest:
        return False
    try:
        return date.fromisoformat(review.get('date', '')) <= date.today()
    except (TypeError, ValueError):
        return False


def edition_rows(work, *, root_dir: Path, profile: dict, manifest: dict, mode: str) -> list[dict]:
    path = root_dir / work['file']
    rows = []
    severity = 'error' if mode == 'release' else 'warning'
    def add(check, message, element=None, *, actual='', hard=False):
        rows.append({'severity': 'error' if hard else severity, 'category': 'ddt_publication',
                     'origin': profile['id'], 'check': 'ddt.' + check,
                     'file': work['file'], 'xml_id': element.get(ID, '') if element is not None else '',
                     'element': element.tag.rsplit('}', 1)[-1] if element is not None else '',
                     'message': message, 'actual': actual})
    if not path.is_file():
        add('manifest_file', 'Selected manifest work does not exist.', hard=True)
        return rows
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        add('parse', str(exc), hard=True)
        return rows
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    ids = {element.get(ID): element for element in root.iter() if element.get(ID)}
    if root.get('meiversion') != profile['meiversion']:
        add('meiversion', 'Edition requires the configured MEI release/customization.', root,
            actual=root.get('meiversion', ''))
    declarations = []
    for raw in re.findall(r'<\?xml-model\s+(.*?)\?>', path.read_text(), flags=re.S):
        declarations.append(dict((name, value) for name, _, value in re.findall(r'([\w:.-]+)\s*=\s*([\'"])(.*?)\2', raw)))
    for syntax in ('http://relaxng.org/ns/structure/1.0', 'http://purl.oclc.org/dsdl/schematron'):
        if not any(d.get('href') == profile['schema_uri'] and d.get('schematypens') == syntax for d in declarations):
            add('schema_declaration', 'Missing exact configured xml-model declaration.', actual=syntax)
    for header_path in profile['required_header_paths']:
        element = find(root, header_path)
        if element is None or not (text(element) or list(element)):
            add('header_field', 'Required edition header field is absent/empty.', actual=header_path)
    availability = find(root, 'meiHead/fileDesc/pubStmt/availability')
    if availability is None or not any(node.get('target') == profile['digital_license_uri'] for node in availability.iter()):
        add('digital_license', 'The MEI-data license must occur in pubStmt/availability; source image rights do not satisfy it.')
    key = find(root, 'meiHead/altId[@type="repository-stem"]')
    if text(key) != work['key']:
        add('edition_key', 'Header local edition key disagrees with the work list.', key, actual=text(key))
    expected_name = 'buxtehude_' + work['key'] + ('.mei' if mode == 'release' else '_corr.mei')
    allowed_names = {expected_name} if mode == 'release' else {expected_name, 'buxtehude_' + work['key'] + '.mei'}
    if path.name not in allowed_names or (mode == 'release' and work['file'] != work['final_file']):
        add('filename', 'File identity does not meet the selected edition mode.', actual=path.name)
    uri = find(root, 'meiHead/fileDesc/pubStmt/identifier[@type="URI"]')
    if text(uri) != profile['public_base_url'] + work['file']:
        add('publication_uri', 'Canonical publication URI disagrees with the actual selected file.', uri, actual=text(uri))
    works = root.findall('m:meiHead/m:workList/m:work', NS)
    if len(works) != 1 or not works[0].get(ID):
        add('principal_work', 'Declare one principal work with a stable ID.')
    else:
        principal = works[0]
        catalogue = principal.find('m:identifier[@type="BuxWV"]', NS)
        # Catalogue identity is per-work; appendix entries may select no BuxWV.
        if work.get('catalogue') and text(catalogue) != work['catalogue']:
            add('catalogue', 'Catalogue identifier disagrees with the work list.', catalogue, actual=text(catalogue))
        for mdiv in root.findall('.//m:music//m:mdiv', NS):
            if '#' + principal.get(ID) not in mdiv.get('decls', '').split():
                add('work_link', 'mdiv must link to the principal work.', mdiv)
    for element in root.iter():
        if element.tag in {f'{{{MEI}}}change', f'{{{MEI}}}annot'}:
            pointers = element.get('resp', '').split()
            if element.tag.endswith('change') and not pointers:
                add('responsibility', 'Revision must name its responsible header declaration.', element)
            for pointer in pointers:
                target = ids.get(pointer.removeprefix('#'))
                if not pointer.startswith('#') or target is None or target.tag != f'{{{MEI}}}respStmt':
                    add('responsibility', 'Edition responsibility must point to a local respStmt.', element, actual=pointer)
    source_desc = find(root, 'meiHead/fileDesc/sourceDesc')
    sources = {} if source_desc is None else {s.get(ID):s for s in source_desc.iter(f'{{{MEI}}}source') if s.get(ID)}
    for source_id in work.get('consulted_sources', []):
        if source_id not in sources:
            add('source_identity', 'Consulted source lacks its addressable bibliography entry.', actual=source_id)
    if work.get('kind') == 'sonata' and str(work.get('opus')) in profile['uppsala_sources']:
        appropriate = profile['uppsala_sources'][str(work['opus'])]
        other = [value for value in profile['uppsala_sources'].values() if value['id'] != appropriate['id']]
        if any(value['id'] in sources for value in other):
            add('opus_source', 'Historical-print source belongs to the other opus.')
        if appropriate['id'] in sources and appropriate['rism'] not in text(sources[appropriate['id']]):
            add('rism', 'Consulted historical-print source lacks its expected RISM identity.', sources[appropriate['id']])
    base = sources.get(profile['base_source_id'])
    if base is not None:
        if profile['base_source_urn'] not in text(base):
            add('base_source_urn', 'Base-edition bibliography lacks the configured URN.', base)
        pages = base.findall('.//m:biblScope[@unit="page"]', NS)
        page_range = work.get('printed_page_range')
        if page_range and not any(all(p.get(k) == v for k,v in page_range.items()) for p in pages):
            add('printed_page_range', 'Printed page range disagrees with the selected work.', base)
    music = root.find('m:music', NS)
    if music is not None:
        missing = Counter(element.tag.rsplit('}',1)[-1] for element in music.iter()
                          if element.tag.rsplit('}',1)[-1] in profile['event_elements'] and not element.get(ID))
        if missing:
            add('event_ids', 'Addressable release events must have persistent IDs.', actual=str(dict(missing)))
        roles = work.get('staff_roles', {})
        staves = {e.get('n') for e in music.iter(f'{{{MEI}}}staff')}
        if set(roles) != staves or any(not role for role in roles.values()):
            add('staff_roles', 'Provide the actual per-work staff role mapping; the pilot mapping is not a corpus default.', actual=str(sorted(staves)))
        prefix = work.get('primary_canvas_prefix')
        surfaces = [e for e in music.iter(f'{{{MEI}}}surface') if prefix and e.get('corresp','').startswith(prefix)]
        if not surfaces:
            add('primary_facsimile', 'Selected work has no configured primary facsimile surfaces.')
        else:
            surface_ids = {e.get(ID) for e in surfaces}
            zone_surface = {z.get(ID):s.get(ID) for s in surfaces for z in s.iter(f'{{{MEI}}}zone') if z.get('type') == 'measure'}
            pagebreaks = [p for p in music.iter(f'{{{MEI}}}pb') if p.get('facs','').removeprefix('#') in surface_ids]
            if [p.get('facs','').removeprefix('#') for p in pagebreaks] != [s.get(ID) for s in surfaces]:
                add('page_sequence', 'Require one primary page break per surface, in source order.')
            for index, surface in enumerate(surfaces, 1):
                if surface.get('n') != str(index):
                    add('surface_number', 'Primary surfaces use a work-local sequence.', surface)
                if not surface.findall('m:graphic', NS):
                    add('primary_graphic', 'Primary surface needs an access graphic.', surface)
            active = None
            for element in music.iter():
                if element.tag == f'{{{MEI}}}pb':
                    if element.get('facs','').removeprefix('#') in surface_ids:
                        active = element.get('facs','').removeprefix('#')
                        expected = next(i for i,s in enumerate(surfaces,1) if s.get(ID) == active)
                        if element.get('n') != str(expected):
                            add('page_number', 'Primary page break number disagrees with its surface.', element)
                if element.tag == f'{{{MEI}}}measure':
                    facs = element.get('facs', '').split()
                    if len(facs) != 1 or facs[0].removeprefix('#') not in zone_surface:
                        add('measure_zone', 'Each measure needs exactly one primary measure-zone pointer.', element)
                    elif zone_surface[facs[0].removeprefix('#')] != active:
                        add('measure_page', 'Measure zone is not on the active primary surface.', element)
            # CAMAT runs its zone-topology checks only in its legacy publication profile.
            uses = Counter(p.removeprefix('#') for m in music.iter(f'{{{MEI}}}measure') for p in m.get('facs', '').split())
            for surface in surfaces:
                box = [surface.get(k) for k in ('ulx', 'uly', 'lrx', 'lry')]
                graphic = surface.find('m:graphic', NS)
                if None in box and graphic is not None:
                    box = ['0', '0', graphic.get('width'), graphic.get('height')]
                for zone in surface.iter(f'{{{MEI}}}zone'):
                    if zone.get('type') != 'measure':
                        continue
                    count = uses[zone.get(ID)]
                    if count == 0:
                        add('unused_measure_zone', 'Measure zone is not referenced by any measure.', zone)
                    elif count > 1:
                        add('shared_measure_zone', 'Measure zone is referenced by more than one measure.', zone, actual=str(count))
                    try:
                        ulx, uly, lrx, lry = (float(zone.get(k)) for k in ('ulx', 'uly', 'lrx', 'lry'))
                        left, top, right, bottom = (float(v) for v in box)
                    except (TypeError, ValueError):
                        continue  # CAMAT reports missing or non-numeric zone coordinates.
                    if ulx < left or uly < top or lrx > right or lry > bottom:
                        add('zone_bounds', 'Measure zone extends beyond its surface.', zone,
                            actual=f'{ulx:g},{uly:g},{lrx:g},{lry:g} outside {left:g},{top:g},{right:g},{bottom:g}')
        for annotation in music.iter(f'{{{MEI}}}annot'):
            if annotation.get('type') != 'editorial':
                continue
            label = annotation.get('label')
            if label not in profile['annotation_labels'] or not text(annotation) or not annotation.get('plist') or not annotation.get('resp'):
                add('annotation_fields', 'Editorial annotation needs category, text, affected-event pointers and responsibility.', annotation)
            if label == 'unresolved-reading':
                add('unresolved_reading', 'Reading remains explicitly unresolved.', annotation)
            if label == 'source-supported-emendation' and not annotation.get('source'):
                add('annotation_evidence', 'Source-supported emendation must identify its attesting witness.', annotation)
            if mode == 'release' and label in {'source-supported-emendation', 'conjectural-emendation'}:
                review = work.get('annotation_reviews', {}).get(annotation.get(ID))
                checks = profile['annotation_review_checks'] + (['witness_locator'] if label == 'source-supported-emendation' else [])
                if not reviewed(review, digest) or not all(review.get('checks', {}).get(check) is True for check in checks):
                    add('annotation_review', 'Source/encoded readings, rationale and evidence require hash-bound human review.', annotation)
    if mode == 'release':
        version = manifest.get('release_version')
        edition = find(root, 'meiHead/fileDesc/editionStmt/edition')
        if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+', version) or edition is None or edition.get('n') != version:
            add('release_version', 'Release edition version must agree with an explicit corpus release version.')
        published_date = find(root, 'meiHead/fileDesc/pubStmt/date')
        if not manifest.get('release_date') or published_date is None or published_date.get('isodate') != manifest['release_date']:
            add('release_date', 'Publication date must agree with the actual declared release date.')
        ref = manifest.get('immutable_git_ref')
        version_uri = find(root, 'meiHead/fileDesc/pubStmt/identifier[@type="versioned-URI"]')
        if not ref or not re.fullmatch(r'[0-9a-f]{40}', ref) or text(version_uri) != profile['public_base_url'].split('/blob/', 1)[0] + '/blob/' + ref + '/' + work['file']:
            add('immutable_uri', 'Release needs an explicit immutable commit URL; no guessed tags are accepted.')
        if work.get('editorial_status') != 'finalized' or not reviewed(work.get('review'), digest) or not all((work.get('review') or {}).get('checks', {}).get(check) is True for check in profile['work_review_checks']):
            add('editorial_review', 'Finalized status needs editor/date sign-off bound to the current input hash.')
    return rows
