from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
from lxml import etree as E
import json,sys

root=Path('/home/egor/Nextcloud/code/public_repos/camat_corpus_editions/DdT_1_vol_11')
score=root/'11_buxtehude_sonatas_final/buxtehude_op2_05_sonata_a_major_corr.mei'
out=Path(Path('/tmp/ddt-op2-05-fresh-review').read_text().strip())/'source-review'
out.mkdir(parents=True,exist_ok=True)
N={'m':'http://www.music-encoding.org/ns/mei'}; ID='{http://www.w3.org/XML/1998/namespace}id'; Q='{'+N['m']+'}'
t=E.parse(str(score)); byid={e.get(ID):e for e in t.iter() if e.get(ID)}
def local(e):return E.QName(e).localname
def meter(e):
 c=e.get('meter.count') or e.get('count'); u=e.get('meter.unit') or e.get('unit')
 if c and u:return F(sum(int(v) for v in c.split('+')))*4/int(u)
 return None
def duration(e,nominal,factor=F(1)):
 name=local(e)
 if name in ['mRest','mSpace']:return nominal
 if name in ['note','rest','chord','space']:
  if e.get('grace'):return F(0)
  v=e.get('dur'); v=v or (e.getparent().get('dur') if name=='note' else None)
  if not v:raise ValueError((name,e.get(ID),'missing duration'))
  d={'breve':F(8),'long':F(16),'maxima':F(32)}.get(v)
  if d is None:d=F(4,int(v))
  dots=int(e.get('dots','0')) or len(e.findall('m:dot',N))
  return d*(2-F(1,2**dots))*factor
 if name=='tuplet':factor*=F(int(e.get('numbase')),int(e.get('num')))
 return sum((duration(c,nominal,factor) for c in e if local(c) in ['note','rest','chord','space','beam','tuplet','mRest','mSpace','bTrem','fTrem']),F(0))
events={}; byvoice=defaultdict(list); abs_time=F(0)
def visit(e,nominal,onset,context,factor=F(1)):
 name=local(e)
 if name in ['note','rest','chord','space','mRest','mSpace']:
  d=duration(e,nominal,factor)
  item={**context,'id':e.get(ID),'kind':name,'onset':str(onset),'absolute_onset':str(abs_time+onset),'duration':str(d),'pitch':(e.get('pname','')+e.get('oct','')) if name=='note' else None,'tie':e.get('tie')}
  if e.get(ID):events[e.get(ID)]=item
  byvoice[(context['staff'],context['layer'])].append(item)
  if name=='chord':
   for n in e.findall('m:note',N):
    if n.get(ID):events[n.get(ID)]={**item,'id':n.get(ID),'kind':'note','pitch':n.get('pname','')+n.get('oct',''),'tie':n.get('tie'),'chord_id':e.get(ID)}
  return onset+d
 if name=='tuplet':factor*=F(int(e.get('numbase')),int(e.get('num')))
 for c in e:
  if local(c) in ['note','rest','chord','space','beam','tuplet','mRest','mSpace','bTrem','fTrem']:onset=visit(c,nominal,onset,context,factor)
 return onset

nominal=None; staff_meters={}; bars=[]; problems=[]; boundaries=[]; current_surface=None; last_x=None; page=0
pending_breaks=[]
for e in t.find('m:music/m:body',N).iter():
 name=local(e)
 if name=='scoreDef':
  v=meter(e)
  ms=e.find('m:meterSig',N)
  if ms is not None:v=meter(ms) or v
  if v is not None:
   nominal=v; staff_meters={k:v for k in ['1','2','3','4','5']}
  for s in e.findall('.//m:staffDef',N):
   v=meter(s); ms=s.find('m:meterSig',N)
   if ms is not None:v=meter(ms) or v
   if v is not None:staff_meters[s.get('n')]=v
  if nominal is None and staff_meters:nominal=next(iter(staff_meters.values()))
 elif name in ['pb','sb']:pending_breaks.append({'kind':name,'id':e.get(ID),'facs':e.get('facs'),'n':e.get('n')})
 elif name=='measure':
  n=int(e.get('n')); lengths={}; zone=byid[e.get('facs','').lstrip('#')]; surface=zone.getparent(); surf=surface.get(ID); x=int(zone.get('ulx')); y=int(zone.get('uly'))
  expected='pb' if surf!=current_surface else ('sb' if last_x is not None and x<last_x-100 else None)
  if expected:boundaries.append({'measure':n,'expected':expected,'surface':surf,'surface_n':surface.get('n'),'actual':pending_breaks})
  elif pending_breaks:boundaries.append({'measure':n,'expected':None,'surface':surf,'actual':pending_breaks})
  current_surface=surf; last_x=x; pending_breaks=[]
  for s in e.findall('m:staff',N):
   sn=s.get('n'); nom=staff_meters.get(sn,nominal)
   for l in s.findall('m:layer',N):
    ln=l.get('n'); d=duration(l,nom); lengths[sn+':'+ln]=str(d)
    visit(l,nom,F(0),{'measure':n,'staff':sn,'layer':ln})
    if d>nom:problems.append({'measure':n,'staff':sn,'layer':ln,'duration':str(d),'meter_quarters':str(nom),'delta':str(d-nom)})
  maximum=max(F(v) for v in lengths.values()); b={'measure':n,'meter_quarters':str(nominal),'metcon':e.get('metcon'),'layer_lengths':lengths,'max_length':str(maximum)}; bars.append(b)
  if maximum<nominal:problems.append({'measure':n,'underfull_all_staves':True,'duration':str(maximum),'meter_quarters':str(nominal)})
  abs_time+=nominal

tie_issues=[]
for tie in t.findall('.//m:tie',N):
 a=events.get(tie.get('startid','').lstrip('#')); b=events.get(tie.get('endid','').lstrip('#'))
 if a and b:
  gap=F(b['absolute_onset'])-(F(a['absolute_onset'])+F(a['duration']))
  if gap!=0 or a['pitch']!=b['pitch']:
   tie_issues.append({'id':tie.get(ID),'start':a,'end':b,'gap':str(gap)})
 else:tie_issues.append({'id':tie.get(ID),'missing':True,'startid':tie.get('startid'),'endid':tie.get('endid')})
inline=defaultdict(list)
for v in events.values():
 if v['kind']=='note' and v['tie']:inline[(v['staff'],v['layer'],v['pitch'])].append(v)
for key,notes in inline.items():
 pending=None
 for n in notes:
  typ=n['tie'].strip()
  if typ in ['t','m']:
   if pending:
    gap=F(n['absolute_onset'])-(F(pending['absolute_onset'])+F(pending['duration']))
    if gap:tie_issues.append({'inline':True,'start':pending,'end':n,'gap':str(gap)})
   else:tie_issues.append({'inline':True,'unpaired_terminal':n})
   pending=None
  if typ in ['i','m']:
   if pending:tie_issues.append({'inline':True,'unpaired_initial':pending})
   pending=n
 if pending:tie_issues.append({'inline':True,'unpaired_initial':pending})
inventory={'measures':len(bars),'surfaces':len(t.findall('.//m:surface',N)),'metcon_false':sum(b['metcon']=='false' for b in bars),'bars':bars,'rhythm_issues':problems,'boundaries':boundaries,'tie_issues':tie_issues}
(out/'audit.json').write_text(json.dumps(inventory,indent=2)+'\n'); (out/'event-inventory.json').write_text(json.dumps(events,indent=2)+'\n')
print(json.dumps({k:inventory[k] for k in ['measures','surfaces','metcon_false','rhythm_issues','tie_issues']},indent=2))
