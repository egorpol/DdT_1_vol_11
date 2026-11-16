from pathlib import Path
from types import SimpleNamespace
from fractions import Fraction as F
from collections import Counter
from copy import deepcopy
from lxml import etree as E
import json,sys,subprocess,hashlib,shutil

root=Path('/home/egor/Nextcloud/code/public_repos/camat_corpus_editions/DdT_1_vol_11');sys.path.insert(0,str(root/'scripts'))
from refresh_editorial_reports import editorial_rows,write_csv,report_path,digest
key='op2_05_sonata_a_major';out=Path(Path('/tmp/ddt-op2-05-final-review').read_text().strip());fresh=Path(Path('/tmp/ddt-op2-05-fresh-review').read_text().strip());backup=Path(Path('/tmp/ddt-op2-05-review-backup').read_text().strip());folder=out/key
record=json.loads((folder/'run.json').read_text());findings=json.loads((folder/'findings.json').read_text());manifest=root/'validation/editorial-works.json';work=next(w for w in json.loads(manifest.read_text())['works'] if w['key']==key);score=root/work['file']
assert record['completion_status']=='completed' and record['mei_conformance']==record['consumer_diagnostics']=='passed'
assert all(e['status']=='passed' for e in record['executions'].values());assert all(i['unchanged'] and i['sha256_after']==digest(score) for i in record['inputs']);assert digest(manifest)==record['ddt']['manifest_sha256']
rows=editorial_rows(SimpleNamespace(record=record,findings=findings),work,root);counts=Counter(r['severity'] for r in rows);assert counts==Counter({'warning':14,'info':2}),counts
write_csv(folder/'editorial.csv',rows);destination=report_path(root,work);destination.write_bytes((folder/'editorial.csv').read_bytes())
summary_path=root/'validation/editorial-reports.json';summary=json.loads(summary_path.read_text());previous=json.loads(summary_path.read_text());index=next(i for i,w in enumerate(summary['works']) if w['work_key']==key);old_entry=summary['works'][index]
camat={k:record['camat'].get(k) for k in ['module_version','distribution_version','git_branch','git_commit','source_tree_sha256']};camat['working_tree_dirty']=bool(record['camat'].get('git_status'))
entry={'work_key':key,'input_file':work['file'],'input_sha256':digest(score),'report_file':str(destination.relative_to(root)),'report_sha256':digest(destination),'completion_status':record['completion_status'],'mei_conformance':record['mei_conformance'],'consumer_diagnostics':record['consumer_diagnostics'],'ddt_publication_acceptance':record['ddt']['publication_acceptance'],'input_unchanged':True,'findings':dict(counts),'checks':{name:{k:v for k,v in e.items() if k in ['requested','required','status','findings_count','reason']} for name,e in record['executions'].items()},'completed_utc':record['finished_utc'],'validation_context':{'camat':camat,'dependency_versions':record['dependency_versions'],'schema':{'file':'schemas/mei-CMN-5.1.rng','sha256':digest(root/'schemas/mei-CMN-5.1.rng')},'sources':{n:digest(root/n) for n in ['validation/editorial-works.json','validation/profile.json','validation/rules.py','scripts/validate_corpus.py','scripts/refresh_editorial_reports.py']},'options':record['options']}}
summary['works'][index]=entry;summary['last_refresh']={'scope':'selected-work','work_keys':[key],'previous_completed_utc':old_entry.get('completed_utc',summary.get('completed_utc')),'retained_work_results':len(summary['works'])-1,'context':'Refreshed work records its own validation_context; other reports were not rerun.'};assert all(w==previous['works'][i] for i,w in enumerate(summary['works']) if i!=index);summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')

# Prove that the documented changes account for the complete music diff.
N={'m':'http://www.music-encoding.org/ns/mei'};Q='{'+N['m']+'}';ID='{http://www.w3.org/XML/1998/namespace}id';parser=E.XMLParser(remove_blank_text=True)
old=E.parse(str(backup/score.name),parser).find('m:music',N);new=E.parse(str(score),parser).find('m:music',N);a={e.get(ID):e for e in old.iter() if e.get(ID)};b={e.get(ID):e for e in new.iter() if e.get(ID)};edits=json.loads((fresh/'edit-evidence.json').read_text());removed={e['id'] for e in edits['removed_spaces']}
assert set(a)-set(b)==removed
for id_,e in a.items():
 if E.QName(e).localname in ['note','rest','chord','beam','tie','slur','zone']:
  f=b[id_];changes={k:(e.get(k),f.get(k)) for k in set(e.attrib)|set(f.attrib) if e.get(k)!=f.get(k)}
  assert not changes or (id_=='g12kqcki' and changes=={'dots':(None,'1')}),(id_,changes)
for item in edits['added_directives']:
 e=b[item['id']];e.getparent().remove(e)
for n in range(1,208):
 om=old.find(f'.//m:measure[@n="{n}"]',N);nm=new.find(f'.//m:measure[@n="{n}"]',N);oh=om.findall('m:harm',N);nh=nm.findall('m:harm',N)
 if n in [41,42]:
  assert len(nh)==1 and len(oh)-len(nh)==(2 if n==41 else 4)
  assert [f.text for f in nh[0].findall('m:fb/m:f',N)]==(['5','♯'] if n==41 else ['♯'])
 else:
  assert len(oh)==len(nh)
  for x,y in zip(oh,nh):
   assert ''.join(x.itertext())==''.join(y.itertext())
   before=dict(x.attrib);after={k:v for k,v in y.attrib.items() if k!=ID or x.get(ID)}
   if n==121 and x.get('startid')=='epyqfsr':assert after=={'startid':'#izvwgne','staff':'3'}
   else:assert before==after,(n,before,after)
 for y in nh:nm.remove(y)
 for x in oh:nm.insert(om.index(x),deepcopy(x))
for id_ in edits['added_tuplets']:
 e=b[id_];parent=e.getparent();i=parent.index(e);children=list(e);parent.remove(e)
 for j,c in enumerate(children):e.remove(c);parent.insert(i+j,c)
for id_ in edits['moved_controls']:
 e=b[id_];orig=a[id_];target=b[orig.getparent().get(ID)];e.getparent().remove(e);target.insert(orig.getparent().index(orig),e)
for e in new.iter():
 id_=e.get(ID)
 if id_ in a:
  orig=a[id_];e.attrib.clear();e.attrib.update(orig.attrib);e.tag=orig.tag;e.text=orig.text
 elif id_:e.attrib.pop(ID,None)
for parent in old.findall('.//m:layer',N):
 target=b[parent.get(ID)]
 for i,child in enumerate(parent):
  if child.get(ID) in removed:target.insert(i,deepcopy(child))
if E.tostring(old,method='c14n')!=E.tostring(new,method='c14n'):
 (fresh/'reverse-expected.xml').write_bytes(E.tostring(old,pretty_print=True))
 (fresh/'reverse-actual.xml').write_bytes(E.tostring(new,pretty_print=True))
 raise AssertionError('Unaccounted music diff; inspect reverse-expected.xml and reverse-actual.xml')
audit=json.loads((fresh/'source-review/audit.json').read_text());assert not audit['rhythm_issues'] and not audit['tie_issues']
for bar in audit['bars']:
 for s in ['1','2','3','4','5']:assert max(F(v) for k,v in bar['layer_lengths'].items() if k.split(':')[0]==s)==F(bar['meter_quarters'])
layout=json.loads((fresh/'source-review/layout-audit.json').read_text());assert layout['score_sha256']==digest(score) and layout['all_source_boundaries_match'] and layout['all_measures_once']

# Preserve every unrelated worktree and staged cleanup entry.
state=json.loads((backup/'state.json').read_text());allowed={work['file'],str(destination.relative_to(root)),'validation/editorial-works.json','validation/editorial-reports.json'};changed=[]
assert subprocess.check_output(['git','ls-files','--stage','-z'],cwd=root,text=True)==state['index'];assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==state['head']
for name,checksum in state['worktree_hashes'].items():
 p=root/name;actual=digest(p) if p.is_file() else None
 if actual!=checksum:changed.append(name)
 assert actual==checksum or name in allowed,name
assert set(changed)==allowed
before_manifest=json.loads((backup/'editorial-works.json').read_text());after_manifest=json.loads(manifest.read_text());assert all(x==y for x,y in zip(before_manifest['works'],after_manifest['works']) if x['key']!=key)
before_reports=json.loads((backup/'editorial-reports.json').read_text());assert all(x==y for x,y in zip(before_reports['works'],summary['works']) if x['work_key']!=key)
proof={'score_sha256':digest(score),'report_sha256':digest(destination),'only_expected_files_changed':sorted(changed),'git_index_preserved':True,'head_unchanged':state['head'],'other_15_work_records_preserved':True,'complete_music_diff_accounted_for':True,'all_original_note_rest_chord_beam_tie_slur_ids_preserved':True,'written_pitches_and_accidentals_preserved':True,'all_staff_totals_match_active_meter':True,'no_tie_timing_mismatches':True,'all_13_pages_51_systems_207_measures_match_source_boundaries':True}
(out/'preservation-evidence.json').write_text(json.dumps(proof,indent=2)+'\n');(out/'layout-audit.json').write_text(json.dumps(layout,indent=2)+'\n');shutil.copy2(fresh/'edit-evidence.json',out/'edit-evidence.json')
for script in ['/tmp/ddt-op2-05-audit.py','/tmp/ddt-op2-05-render.py']:
 shutil.copy2(script,out/Path(script).name)
(out/'review-notes.md').write_text(f'''# Op. II/5 review — 2026-10-20

Sonata V in A major, Op. II, BuxWV 263; DdT pp. 126–138, BSB images and
canvases 136–148. Catalogue identity agrees with Edition Güntersberg G115:
https://www.guentersberg.de/noten/de/g111.php . The header credits You Zhou and
Egor Polyakov from the actual correction history. DdT is the documented basis
for these repairs; no historical-facsimile comparison is claimed or needed for
them. The working edition is 0.1.0, with the existing 2019 encoding date and
Verovio conversion record retained. Earlier repository correction dates are
recorded separately from the current review.

## Corrections against DdT

- Replaced six misclassified figured-bass controls above the violin with proper
  6:4 sextuplets in mm. 41–42 (DdT p. 128); retained every original beam and note.
  Restored the three printed tuplet numerals in m. 130 (p. 133).
- Corrected the m. 41 figured-bass reading from 6 to the printed 5/sharp stack.
- Fixed the malformed Solo reference in m. 120 and encoded it as a direction.
  Attached the m. 121 5-flat figure to the correct beat-3 continuo note, rather
  than to the preceding bar's gamba note.
- Restored the missing dot on the keyboard bass's opening half note in m. 124
  (p. 132). No written pitch or accidental changed.
- Removed 95 surplus hidden spaces, including the excess initial sixteenth in
  the violin's second layer in m. 193. Necessary voice-alignment spaces remain.
  All staves now fill their active meters; short subsidiary voices may end early.
- Corrected both m. 135 Adagio labels to the printed Allegro. and restored the
  a 2. direction above the gamba (p. 133, third system).
- Moved the two Adagio controls from m. 169 into their target measure 168.
  Matched directly checked punctuation for Allegro., Adagio. and Poco Presto.
  Preserved the source distinction in m. 171: (Presto.) above violin and
  Presto. above the keyboard realization (p. 135).
- Restored the closing Da capo se piace. direction (p. 138), without introducing
  an automatic playback repeat.
- Corrected eight false page breaks to system breaks before mm. 10, 30, 39,
  57, 88, 139, 183 and 205. Preserved their IDs and every original boundary
  position. Numbered the thirteen actual page breaks and linked all surfaces
  to verified BSB IIIF canvases. Added persistent IDs to previously unlabelled
  events and linked the music division to its work identity.

These are repairs to match DdT. No conjectural emendation or new upstream bug
report is proposed. The existing source pitches, accidentals, note/rest/chord
and beam IDs, ties, slurs and facsimile-zone geometry are retained.

## Checks and limits

Fresh baseline: 2 errors, 24 warnings, 2 informational notices.
Final: **0 errors, 14 warnings, 2 informational notices**. All executions pass:
XML references, MEI 5.1 CMN Relax NG, Schematron, resources, all thirteen public
image URLs, Verovio all-page rendering, CAMAT parsing and input hashes.
The warnings comprise thirteen external-IIIF Schematron advisories and the
publication-review reminder. The notices concern the source's two Presto
spellings; they are retained intentionally.

The independent audit bypasses all 95 existing metcon=false flags. Every staff
in all 207 measures has the nominal overall duration in its current meter,
with no overfull layer and no tie-timing mismatch. Existing metcon flags remain.
All thirteen page comparisons were visually inspected for source boundaries
and the identified notation issues. Rendering contains 13 pages, 51 systems
and each measure 1–207 once. This targeted consistency/source review is not a
claim of full note-by-note collation of every printed event.

Some figured-bass accidental text displays with substituted glyphs in local
PNG conversion because of the music-font fallback. This is recorded as a local
preview limitation, not classified as a new score or upstream defect.

## Evidence and preservation

Source images, checksums, crops, final SVG/PNG comparisons and rhythm/event
audits are in `{fresh.relative_to(root)}/source-review/`.
This final run contains its validator output, exported CSV, edit inventory,
layout audit and preservation proof. Reversing precisely the documented edits
reproduces the baseline music tree. The tracked CSV hashes match this validated
score, and the other fifteen work records and all unrelated working files and
the entire Git index are unchanged.

Op. II/4 was committed and pushed separately as 79b088f5, with exactly its MEI
and CSV. Op. II/5 remains local and uncommitted; publication acceptance remains
needs-review. No further source decision is required for the repairs above.
''',encoding='utf-8')
print(json.dumps({'findings':dict(counts),'score_sha256':entry['input_sha256'],'report_sha256':entry['report_sha256'],'preservation':'passed','review_notes':str(out/'review-notes.md')},indent=2))
