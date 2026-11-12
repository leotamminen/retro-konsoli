"""Truthful difficulty bot: directional charged shots + dodge. ONLY HP refill assist."""
from lib import *
import json,random
RESULT=[];LIMIT=int(os.environ.get('VELLAMO_BOT_FRAMES','22000'))
for name,bf in [('joukahainen','b10'),('ahti','b11'),('aino','b12'),('vellamo','b13')]:
 for diff in G['DIFFS']:
  g=new_game();sv=G['new_save']('hunter');sv.update(vellamo_unlocked=True,vellamo_visited=True,bonfire=bf);pad=start(g,'hunter',save=sv,bonfire=bf,diff=diff);g.start_boss(name);b=g.boss
  assists=arrows=0;peak=1;deaths=g.save['deaths'];random.seed(123)
  for frame in range(LIMIT):
   if g.state_name!='play' or g.save['deaths']>deaths:break
   peak=max(peak,int(b.phase));pl=g.players[0];a=G['ARENAS'][name];left=a['x0']*16+32;right=a['x1']*16-20
   face=1 if b.x>=pl.x else -1;threats=[z for z in g.zones if z.active and abs(pl.x-z.x)<40]
   desired=left if b.x-left>140 else right
   # Charge facing enemy; dodge out of real warning/active ground zones.
   c=pad.blank();charge=frame%90<62;c['skill']=charge;c['x']=face;c['right']=face==1;c['left']=face==-1
   if (frame%29)<10:
    c['x']=1 if pl.x<desired else -1;c['right']=c['x']>0;c['left']=c['x']<0
   if threats and pl.stam>18 and pl.state=='free' and frame%33<2:c['dodge']=True
   if frame%81<3:c['x']=face;c['right']=face==1;c['left']=face==-1
   if frame%90==0:pl.hp=pl.maxhp;pl.inv=55;assists+=1
   previous={id(q) for q in g.projs};pad.nextc=c;step(g,1,False)
   arrows+=sum(q.kind=='parrow' and id(q) not in previous for q in g.projs)
   won=(name in ('joukahainen','ahti') and g.felled and g.felled[0]==name) or (name=='aino' and g.state_name=='aino_reveal') or (name=='vellamo' and g.save.get('aino_freed'))
   if won:break
  won=(name in ('joukahainen','ahti') and g.felled and g.felled[0]==name) or (name=='aino' and g.state_name=='aino_reveal') or (name=='vellamo' and g.save.get('aino_freed'))
  result=dict(boss=name,difficulty=diff,won=bool(won),frames=frame+1,assists=assists,assist='HP full +55 i-frames every 90 frames. Not an unassisted victory; no boss HP edits, boost, teleports, artificial kills.',arrows=arrows,max_phase=peak,state=g.state_name,hp=int(b.hp),boss_initial_hp=float(b.maxhp),died=g.save['deaths']>deaths)
  RESULT.append(result);print(json.dumps(result),flush=True)
open('vellamo_bot_results.json','w').write(json.dumps(RESULT,indent=2))
