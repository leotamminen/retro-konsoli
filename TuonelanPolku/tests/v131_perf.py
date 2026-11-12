from lib import *
import time, random, statistics, json, gc
out=[];random.seed(402)
def run(label,g,p,frames=1500,phase=None):
 vals=[];start=time.perf_counter()
 for i in range(frames):
  c=p.blank();c['right']=i%200<80;c['left']=80<=i%200<180;c['x']=1 if c['right'] else -1 if c['left'] else 0;c['jump']=i%71==0;c['light']=i%31<2;c['dodge']=i%121==15
  if phase:
   if g.boss and g.boss.dead:g.boss.invuln=True
   if g.boss is None:break
   if g.boss:g.boss.hp=g.boss.maxhp;g.boss.phase=phase;g.boss.invuln=False
   if i==0 and phase>=2:g.boss.invuln=True
  if g.state_name!='play':c={}
  p.nextc=c;t=time.perf_counter();g.update();g.draw();vals.append((time.perf_counter()-t)*1000)
 print('%-26s mean %.3f p99 %.3f max %.3f >16.7 %s'%(label,statistics.mean(vals),sorted(vals)[int(len(vals)*.99)],max(vals),sum(x>16.7 for x in vals)),flush=True)
 out.append(dict(scene=label,frames=frames,mean=statistics.mean(vals),p99=sorted(vals)[int(len(vals)*.99)],worst=max(vals),over_budget=sum(x>16.7 for x in vals)))
for bf,ar in [('b10','ranta'),('b11','syvanne'),('b12','katedraali')]:
 g=new_game();sv=G['new_save']('hunter');sv.update(vellamo_unlocked=True,vellamo_visited=True,bonfire=bf);p=start(g,'hunter',save=sv,bonfire=bf);pp=ScriptPad('p2');g.add_pad(pp);g.add_p2('sage',pp);run('coop '+ar,g,p)
for key,bf in [('joukahainen','b10'),('ahti','b11'),('aino','b12'),('vellamo','b13')]:
 for ph in ({'joukahainen':(1,2),'ahti':(1,2),'aino':(1,2,3),'vellamo':(1,2,3)}[key]):
  g=new_game();sv=G['new_save']('hunter');sv.update(vellamo_unlocked=True,vellamo_visited=True,bonfire=bf);p=start(g,'hunter',save=sv,bonfire=bf);g.start_boss(key);run(key+':phase'+str(ph),g,p,900,ph)
with open(os.environ.get('TP_PERF_JSON', 'artifacts/v131_perf.json'),'w') as f:json.dump(out,f,indent=2)
allvals=out;print('OVERALL mean %.3f worst %.3f'% (statistics.mean([r['mean'] for r in allvals]),max(r['worst'] for r in allvals)),flush=True)
