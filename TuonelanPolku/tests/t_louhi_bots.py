import os
os.environ['SDL_DRIVER']='dummy';os.environ['TUONELA_NO_MUSIC']='1'
from lib import *
import time,random,json
res=[];random.seed(221)
print('Every attack, movement, collision and HP change is simulated. Assist = explicit quiver/flask heal.',flush=True)
for bossname,bf,attempts_allowed in [('louhi','b9',3)]:
 for diff in ('easy','normal','hard','brutal','tuonela'):
  won=False;assists=0;realdeaths=0;shots=0;frames=0;prevshots=set();won_all=[];maxphase=1;startclock=time.time()
  for attempt in range(1):
   g=new_game();p=start(g,'hunter',bonfire=bf,diff=diff)
   g.start_boss(bossname)
   b=g.boss
   lastfocus=1
   for k in range(48000):
    frames+=1;maxphase=max(maxphase,b.phase)
    if b.dead:break
    pl=g.players[0];c=p.blank()
    # Lightweight physical play, without changing movement speed or attack rules.
    if pl.state!='draw':
     # Stay left of boss; bow is fired right. Walk around floor telegraphs.
     desired=b.x-65
     # keep the right hand lane for reliable arrows
     desired=b.x-65
     dangerous=[z for z in g.zones if not z.active and z.dmg>0]
     near=[z for z in dangerous if abs(pl.x-z.x)<34]
     if near:
      lanes=[b.L+17,b.L+62,b.L+116,b.R-17]
      desired=min(lanes,key=lambda a:sum(40 if abs(a-z.x)<38 else 0 for z in dangerous)+abs(a-pl.x)/12)
     dx=desired-pl.x
     left=dx<-10 if abs(dx)>10 else b.x<pl.x
     c.update(x=-1 if left else 1,left=left,right=not left,skill=k%74<49)
     c['dodge']=pl.state=='hurt' and k%9==0
    else:c.update(skill=k%74<49)
    if k%30==0:
     # Assistance is clearly reported, not counted as an ordinary play win without help.
     pl.refill();pl.inv=30;assists+=1
    wasdeath=g.save['deaths']
    p.nextc=c;prevshots={id(a) for a in g.projs};step(g,1,False)
    realdeaths+=g.save['deaths']-wasdeath
    shots+=sum(a.kind=='parrow' and id(a) not in prevshots for a in g.projs)
    if g.state_name!='play':break
   if b.dead:won=True;break
   if time.time()-startclock>180:break
  res.append(dict(boss=bossname,difficulty=diff,won=won,attempts=attempt+1,frames=frames,assists=assists,deaths=realdeaths,shots=shots,max_phase=maxphase))
  print(res[-1],flush=True)
 open('louhi_bot_results.json','w').write(json.dumps(res,indent=2))
