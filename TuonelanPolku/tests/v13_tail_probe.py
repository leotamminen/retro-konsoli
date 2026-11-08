from lib import *
import time,random,gc,statistics
random.seed(44)
for bf in ['b7','b9']:
 g=new_game();p=start(g,bonfire=bf);p2=ScriptPad('p2');g.add_pad(p2);g.add_p2('hunter',p2)
 gcstats=[x['collections'] for x in gc.get_stats()];records=[];before=[0,0]
 for i in range(4000):
  c=p.blank();c['right']=i%220<110;c['left']=110<=i%220<220;c['x']=1 if c['right'] else -1 if c['left'] else 0;c['jump']=i%80==0;c['light']=i%42<2;c['dodge']=i%140==17;p.nextc=c
  oldchunks=len(G['GameCore'].CHUNK_CACHE);t=time.perf_counter();g.update();tu=(time.perf_counter()-t)*1000;t=time.perf_counter();g.draw();td=(time.perf_counter()-t)*1000
  now=[x['collections'] for x in gc.get_stats()]
  if tu+td>12:records.append(dict(i=i,u=tu,d=td,total=tu+td,p=[round(q.x) for q in g.players],boss=bool(g.boss),chunk_added=len(G['GameCore'].CHUNK_CACHE)!=oldchunks,chunks=len(g.chunks),gc_delta=[a-b for a,b in zip(now,before)]))
  before=now
 print(bf,'OUTLIERS',records,flush=True)
