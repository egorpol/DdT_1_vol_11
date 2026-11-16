from pathlib import Path
from lxml import etree as E
from PIL import Image,ImageOps,ImageDraw
import verovio,json,subprocess,hashlib

root=Path('/home/egor/Nextcloud/code/public_repos/camat_corpus_editions/DdT_1_vol_11');score=root/'11_buxtehude_sonatas_final/buxtehude_op2_05_sonata_a_major_corr.mei'
out=Path(Path('/tmp/ddt-op2-05-fresh-review').read_text().strip())/'source-review';out.mkdir(exist_ok=True)
t=E.parse(str(score));N={'m':'http://www.music-encoding.org/ns/mei','s':'http://www.w3.org/2000/svg'};ID='{http://www.w3.org/XML/1998/namespace}id'
audit=json.loads((out/'audit.json').read_text());expected=[]
for b in audit['boundaries']:
 if b['expected']=='pb':expected.append({'page':len(expected)+1,'printed_page':125+len(expected)+1,'start_measure':b['measure'],'systems':[]})
 expected[-1]['systems'].append(b['measure'])
measures={e.get(ID):int(e.get('n')) for e in t.findall('.//m:measure',N)}
tk=verovio.toolkit();options={'breaks':'encoded','pageWidth':3000,'pageHeight':4500,'adjustPageHeight':True,'scale':40,'header':'none','footer':'none','svgViewBox':True,'spacingStaff':10,'spacingSystem':8}
tk.setOptions(options);assert tk.loadFile(str(score));assert tk.getPageCount()==13,tk.getPageCount();seen=[];layout=[]
for page in range(1,14):
 svg=tk.renderToSVG(page);path=out/f'final-page-{page:02d}.svg';path.write_text(svg);doc=E.fromstring(svg.encode());systems=[];page_measures=[]
 for system in doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," system ")]'):
  ids=[e.get('id') for e in system.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," measure ")]')];ns=[measures[x] for x in ids if x in measures]
  if ns:systems.append(ns[0]);page_measures+=ns
 assert systems==expected[page-1]['systems'],(page,systems,expected[page-1])
 seen+=page_measures;layout.append({**expected[page-1],'measures':page_measures})
 png=out/f'final-page-{page:02d}.png';subprocess.run(['rsvg-convert','-b','white','-w','1250','-o',str(png),str(path)],check=True)
 src=Image.open(out/f'ddt-image-{135+page}.jpg').convert('RGB');src.thumbnail((1250,1900));ren=Image.open(png).convert('RGB');ren.thumbnail((1250,1900));height=max(src.height,ren.height)+35;pair=Image.new('RGB',(2500,height),'white');pair.paste(src,((1250-src.width)//2,35));pair.paste(ren,(1250+(1250-ren.width)//2,35));d=ImageDraw.Draw(pair);d.text((10,10),f'DdT p. {125+page}',fill='black');d.text((1260,10),f'Op. II/5 final rendering, page {page}',fill='black');pair.save(out/f'comparison-page-{page:02d}.png')
assert sorted(seen)==list(range(1,208)) and len(seen)==len(set(seen))==207
for first,last in [(41,42),(120,121),(124,124),(130,130),(135,135),(168,169),(180,181),(193,193)]:
 v=verovio.toolkit();v.setOptions({**options,'breaks':'none','pageWidth':2500,'pageHeight':3000});assert v.loadFile(str(score));assert v.select({'measureRange':f'{first}-{last}'});v.redoLayout();path=out/f'final-m{first}-{last}.svg';path.write_text(v.renderToSVG(1));png=path.with_suffix('.png');subprocess.run(['rsvg-convert','-b','white','-w','1700','-o',str(png),str(path)],check=True);im=Image.open(png).convert('RGB');bbox=ImageOps.invert(im).getbbox();im.crop((max(0,bbox[0]-15),max(0,bbox[1]-15),min(im.width,bbox[2]+15),min(im.height,bbox[3]+15))).save(png)
(out/'layout-audit.json').write_text(json.dumps({'score_sha256':hashlib.sha256(score.read_bytes()).hexdigest(),'pages':13,'systems':sum(len(p['systems']) for p in expected),'measures':207,'all_source_boundaries_match':True,'all_measures_once':True,'details':layout},indent=2)+'\n')
print('Final layout: 13 pages, 51 systems, all 207 measures once; targeted snippets rendered.')
